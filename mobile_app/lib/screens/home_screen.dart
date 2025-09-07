import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'dart:convert';
import 'dart:io';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../spotify_auth_screen.dart';

class HomeScreen extends StatefulWidget {
  final bool isAuthenticated;

  const HomeScreen({super.key, required this.isAuthenticated});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  File? _selectedImage;
  bool _isLoading = false;
  bool _isSpotifyAuthorized = false;
  Map<String, dynamic>? _analysisResult;
  Map<String, dynamic>? _recommendations;
  String _debugInfo = '';

  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _isSpotifyAuthorized = widget.isAuthenticated;
    _checkBackendConnection();
  }

  void _addDebugInfo(String info) {
    setState(() {
      _debugInfo += '$info\n';
    });
    print('DEBUG: $info');
  }

  Future<void> _checkBackendConnection() async {
    _addDebugInfo('Checking backend connection...');
    try {
      final response = await http.get(Uri.parse('${Config.baseUrl}/health'));
      _addDebugInfo('Health check response: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _addDebugInfo('Health data: ${data.toString()}');

        setState(() {
          _isSpotifyAuthorized =
              widget.isAuthenticated || (data['user_authenticated'] ?? false);
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✅ Connected to backend!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }
    } catch (e) {
      _addDebugInfo('Backend connection error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Backend connection failed: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 80,
        maxWidth: 1920,
        maxHeight: 1080,
      );
      if (image != null) {
        _addDebugInfo('Image selected: ${image.path}');
        setState(() {
          _selectedImage = File(image.path);
          _analysisResult = null;
          _recommendations = null;
        });
      }
    } catch (e) {
      _addDebugInfo('Image picker error: $e');
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to pick image: $e')));
    }
  }

  Future<void> _analyzeImage() async {
    if (_selectedImage == null) return;

    setState(() {
      _isLoading = true;
    });

    _addDebugInfo('Starting image analysis...');

    try {
      // Validate file exists and can be read
      if (!await _selectedImage!.exists()) {
        throw Exception('Selected image file does not exist');
      }

      final fileSize = await _selectedImage!.length();
      _addDebugInfo('File size: $fileSize bytes');

      if (fileSize == 0) {
        throw Exception('Selected image file is empty');
      }

      if (fileSize > 10 * 1024 * 1024) {
        throw Exception('Image file is too large (${fileSize} bytes)');
      }

      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${Config.baseUrl}/analyze-image'),
      );

      _addDebugInfo('Adding file to request: ${_selectedImage!.path}');

      final fileBytes = await _selectedImage!.readAsBytes();
      _addDebugInfo('File read: ${fileBytes.length} bytes');

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: 'mobile_image.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      request.headers['Accept'] = 'application/json';
      request.headers['User-Agent'] = 'Flutter Mobile App';

      _addDebugInfo('Sending request to: ${Config.baseUrl}/analyze-image');
      final response = await request.send().timeout(
        const Duration(seconds: 60),
        onTimeout: () {
          _addDebugInfo('Request timed out after 60 seconds');
          throw Exception('Request timed out');
        },
      );
      final responseData = await response.stream.bytesToString();

      _addDebugInfo('Response status: ${response.statusCode}');
      _addDebugInfo('Response data: $responseData');

      if (response.statusCode == 200) {
        final result = json.decode(responseData);
        _addDebugInfo('Parsed result: ${result.toString()}');

        setState(() {
          _analysisResult = result;
        });

        // Automatically get recommendations after analysis
        if (result['mood'] != null && result['caption'] != null) {
          await _getRecommendations(result['mood'], result['caption']);
        } else {
          _addDebugInfo('Missing mood or caption in result');
        }
      } else {
        _addDebugInfo('Analysis failed with status: ${response.statusCode}');
        String errorDetail = 'Unknown error';
        try {
          final errorJson = json.decode(responseData);
          errorDetail =
              errorJson['detail'] ?? errorJson['message'] ?? responseData;
        } catch (parseError) {
          errorDetail = responseData.isEmpty ? 'Empty response' : responseData;
        }

        _addDebugInfo('Error detail: $errorDetail');
        throw Exception(
          'Analysis failed: ${response.statusCode} - $errorDetail',
        );
      }
    } catch (e) {
      _addDebugInfo('Analysis error: $e');
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Analysis failed: $e')));
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _getRecommendations(String mood, String caption) async {
    _addDebugInfo('Getting recommendations for mood: $mood, caption: $caption');

    try {
      final response = await http.post(
        Uri.parse('${Config.baseUrl}/mixed-recommendations'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'mood': mood, 'caption': caption}),
      );

      _addDebugInfo('Recommendations response: ${response.statusCode}');
      _addDebugInfo('Recommendations data: ${response.body}');

      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        setState(() {
          _recommendations = result;
        });
      } else {
        throw Exception(
          'Recommendations failed: ${response.statusCode} - ${response.body}',
        );
      }
    } catch (e) {
      _addDebugInfo('Recommendations error: $e');
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Recommendations failed: $e')));
    }
  }

  Future<void> _authorizeSpotify() async {
    _addDebugInfo('Starting Spotify authorization...');

    try {
      final result = await Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const SpotifyAuthScreen()),
      );

      if (result == true) {
        _addDebugInfo('Spotify authentication successful!');
        setState(() {
          _isSpotifyAuthorized = true;
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✅ Spotify connected successfully!'),
              backgroundColor: Colors.green,
            ),
          );
        }

        await _checkSpotifyTokenStatus();
        await _checkBackendConnection();
      } else {
        _addDebugInfo('Spotify authentication cancelled or failed');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('❌ Spotify authentication failed'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      _addDebugInfo('Spotify auth error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Spotify authorization failed: $e')),
      );
    }
  }

  Future<void> _checkSpotifyTokenStatus() async {
    _addDebugInfo('Checking Spotify token status...');

    try {
      final response = await http.get(
        Uri.parse('${Config.baseUrl}/spotify/status'),
      );

      _addDebugInfo('Token status response: ${response.statusCode}');
      _addDebugInfo('Token status data: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final hasToken = data['has_token'] ?? false;
        final userCount = data['user_count'] ?? 0;

        _addDebugInfo(
          'Has valid token: $hasToken, Users with tokens: $userCount',
        );
      }
    } catch (e) {
      _addDebugInfo('Token status check error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🎵 Image-to-Song'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.bug_report),
            onPressed: () => _showDebugDialog(),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Authentication Status Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Icon(
                          _isSpotifyAuthorized
                              ? Icons.verified
                              : Icons.music_note,
                          size: 32,
                          color: _isSpotifyAuthorized
                              ? Colors.green
                              : Colors.grey,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _isSpotifyAuthorized
                                    ? 'Spotify Connected!'
                                    : 'Anonymous Mode',
                                style: Theme.of(context).textTheme.titleMedium
                                    ?.copyWith(
                                      color: _isSpotifyAuthorized
                                          ? Colors.green
                                          : Colors.grey[600],
                                    ),
                              ),
                              Text(
                                _isSpotifyAuthorized
                                    ? 'Getting personalized recommendations'
                                    : 'Getting general mood-based recommendations',
                                style: Theme.of(context).textTheme.bodySmall
                                    ?.copyWith(color: Colors.grey[600]),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    if (!_isSpotifyAuthorized) ...[
                      const SizedBox(height: 12),
                      ElevatedButton.icon(
                        onPressed: _authorizeSpotify,
                        icon: const Icon(Icons.music_note),
                        label: const Text('Connect Spotify for Better Results'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1DB954),
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Image Selection Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    if (_selectedImage == null)
                      Container(
                        height: 200,
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: InkWell(
                          onTap: _pickImage,
                          child: const Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.add_photo_alternate,
                                  size: 48,
                                  color: Colors.grey,
                                ),
                                SizedBox(height: 8),
                                Text('Tap to select an image'),
                              ],
                            ),
                          ),
                        ),
                      )
                    else
                      Column(
                        children: [
                          Container(
                            height: 200,
                            width: double.infinity,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: Image.file(
                                _selectedImage!,
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: ElevatedButton(
                                  onPressed: _pickImage,
                                  child: const Text('Change Image'),
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: ElevatedButton(
                                  onPressed:
                                      _isLoading || _selectedImage == null
                                      ? null
                                      : _analyzeImage,
                                  child: _isLoading
                                      ? const SizedBox(
                                          height: 20,
                                          width: 20,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Text('🤖 Analyze'),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                  ],
                ),
              ),
            ),

            // Analysis Results
            if (_analysisResult != null) ...[
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '🎯 AI Analysis',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text('Caption: ${_analysisResult!['caption']}'),
                      Text('Mood: ${_analysisResult!['mood']}'),
                      Text(
                        'Confidence: ${((_analysisResult!['confidence'] ?? 0.5) * 100).toStringAsFixed(1)}%',
                      ),
                    ],
                  ),
                ),
              ),
            ],

            // Recommendations
            if (_recommendations != null) ...[
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '🎵 Your ${_isSpotifyAuthorized ? "Personalized" : "Mood-Based"} Recommendations',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 16),

                      // Personalized recommendations (only if authenticated)
                      if (_recommendations!['personalized']?.isNotEmpty ==
                          true) ...[
                        const Text(
                          '🔥 Personalized',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        ..._buildTrackList(_recommendations!['personalized']),
                        const SizedBox(height: 16),
                      ],

                      // Mood-based recommendations
                      if (_recommendations!['mood_based']?.isNotEmpty ==
                          true) ...[
                        Text(
                          _isSpotifyAuthorized
                              ? '🎭 Mood-Based'
                              : '🎭 Recommendations',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        ..._buildTrackList(_recommendations!['mood_based']),
                        const SizedBox(height: 16),
                      ],

                      // Discovery recommendations
                      if (_recommendations!['discovery']?.isNotEmpty ==
                          true) ...[
                        const Text(
                          '🌟 Discovery',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        ..._buildTrackList(_recommendations!['discovery']),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showDebugDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Debug Information'),
        content: SingleChildScrollView(
          child: Text(
            _debugInfo,
            style: const TextStyle(fontSize: 10, fontFamily: 'monospace'),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          TextButton(
            onPressed: () {
              setState(() {
                _debugInfo = '';
              });
              Navigator.pop(context);
            },
            child: const Text('Clear'),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildTrackList(List<dynamic> tracks) {
    return tracks
        .map(
          (track) => Card(
            margin: const EdgeInsets.symmetric(vertical: 4),
            child: ListTile(
              title: Text(track['name'] ?? 'Unknown Track'),
              subtitle: Text(
                '${track['artist'] ?? 'Unknown Artist'} ${track['popularity'] != null ? "• Popularity: ${track['popularity']}/100" : ""}',
              ),
              trailing: IconButton(
                icon: const Icon(Icons.open_in_new),
                onPressed: () => _openSpotifyTrack(
                  track['spotify_url'] ?? track['external_url'],
                ),
              ),
            ),
          ),
        )
        .toList();
  }

  Future<void> _openSpotifyTrack(String? url) async {
    if (url != null && url.isNotEmpty && url != '#') {
      try {
        if (await canLaunchUrl(Uri.parse(url))) {
          await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
        }
      } catch (e) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Could not open track: $e')));
      }
    }
  }
}
