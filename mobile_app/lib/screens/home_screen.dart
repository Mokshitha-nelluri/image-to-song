import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:url_launcher/url_launcher.dart';
import '../models/user_music_profile.dart';
import '../models/song_recommendation.dart';
import '../services/api_service.dart';
import '../services/profile_service.dart';
import '../services/audio_service.dart';
import 'quiz_screen.dart';

class HomeScreen extends StatefulWidget {
  final UserMusicProfile? userProfile;

  const HomeScreen({super.key, this.userProfile});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  final ProfileService _profileService = ProfileService();
  final AudioService _audioService = AudioService();
  final ImagePicker _picker = ImagePicker();

  File? _selectedImage;
  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;
  List<SongRecommendation>? _recommendations;
  UserMusicProfile? _userProfile;

  @override
  void initState() {
    super.initState();
    _userProfile = widget.userProfile;
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    try {
      if (_userProfile == null) {
        _userProfile = await _profileService.loadProfile();
        setState(() {});
      }
    } catch (e) {
      print('Error loading user profile: $e');
    }
  }

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _analysisResult = null;
          _recommendations = null;
        });
      }
    } catch (e) {
      _showErrorSnackBar('Failed to pick image: $e');
    }
  }

  Future<void> _takePhoto() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 85,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _analysisResult = null;
          _recommendations = null;
        });
      }
    } catch (e) {
      _showErrorSnackBar('Failed to take photo: $e');
    }
  }

  Future<void> _analyzeImage() async {
    if (_selectedImage == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // Analyze image
      final imageBytes = await _selectedImage!.readAsBytes();
      final analysisResult = await _apiService.analyzeImage(
        imageBytes,
        'mobile_image.jpg',
      );

      setState(() {
        _analysisResult = analysisResult;
      });

      // Get recommendations based on mood and user profile
      final mood = analysisResult['mood'] ?? 'neutral';
      final caption = analysisResult['caption'] ?? '';

      final recommendations = await _apiService.getRecommendations(
        mood: mood,
        caption: caption,
        userProfile: _userProfile,
      );

      setState(() {
        _recommendations = recommendations;
      });
    } catch (e) {
      _showErrorSnackBar('Analysis failed: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showErrorSnackBar(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: Colors.red),
      );
    }
  }

  void _navigateToQuiz() {
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (context) => const QuizScreen()));
  }

  Future<void> _openSpotifyTrack(String url) async {
    try {
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      }
    } catch (e) {
      _showErrorSnackBar('Could not open track: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF191414), // Spotify dark
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          '🎵 Image-to-Song',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.quiz, color: Colors.white),
            onPressed: _navigateToQuiz,
            tooltip: 'Retake Quiz',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // User profile card
            if (_userProfile != null) _buildProfileCard(),

            const SizedBox(height: 16),

            // Image upload card
            _buildImageUploadCard(),

            // Analysis results
            if (_analysisResult != null) ...[
              const SizedBox(height: 16),
              _buildAnalysisCard(),
            ],

            // Recommendations
            if (_recommendations != null && _recommendations!.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildRecommendationsCard(),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProfileCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1DB954), Color(0xFF1ed760)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.person, color: Colors.white, size: 24),
              const SizedBox(width: 12),
              const Text(
                'Your Music Profile',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.edit, color: Colors.white, size: 20),
                onPressed: _navigateToQuiz,
                tooltip: 'Edit Profile',
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            _userProfile!.musicPersonality,
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _buildProfileStat('Songs Liked', '${_userProfile!.songsLiked}'),
              const SizedBox(width: 20),
              _buildProfileStat(
                'Top Genre',
                _userProfile!.topGenres.isNotEmpty
                    ? _userProfile!.topGenres.first.key.toUpperCase()
                    : 'MIXED',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildProfileStat(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildImageUploadCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1), width: 1),
      ),
      child: Column(
        children: [
          const Row(
            children: [
              Icon(Icons.photo_camera, color: Colors.white, size: 24),
              SizedBox(width: 12),
              Text(
                'Upload Your Photo',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          if (_selectedImage == null)
            Container(
              height: 200,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Colors.white.withOpacity(0.2),
                  width: 2,
                  style: BorderStyle.solid,
                ),
              ),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.add_photo_alternate,
                      size: 48,
                      color: Colors.white.withOpacity(0.6),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Select a photo to get music recommendations',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 16,
                      ),
                    ),
                  ],
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
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.file(_selectedImage!, fit: BoxFit.cover),
                  ),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: _isLoading ? null : _analyzeImage,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1DB954),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(25),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text(
                          '🎵 Get Music Recommendations',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                ),
              ],
            ),

          const SizedBox(height: 16),

          // Action buttons
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _pickImage,
                  icon: const Icon(Icons.photo_library, color: Colors.white),
                  label: const Text(
                    'Gallery',
                    style: TextStyle(color: Colors.white),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.white),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _takePhoto,
                  icon: const Icon(Icons.camera_alt, color: Colors.white),
                  label: const Text(
                    'Camera',
                    style: TextStyle(color: Colors.white),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.white),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAnalysisCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.psychology, color: Colors.white, size: 24),
              SizedBox(width: 12),
              Text(
                'AI Analysis',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildAnalysisItem('Mood', _analysisResult!['mood'] ?? 'Unknown'),
          const SizedBox(height: 8),
          _buildAnalysisItem(
            'Description',
            _analysisResult!['caption'] ?? 'No description',
          ),
          const SizedBox(height: 8),
          _buildAnalysisItem(
            'Confidence',
            '${((_analysisResult!['confidence'] ?? 0.5) * 100).round()}%',
          ),
        ],
      ),
    );
  }

  Widget _buildAnalysisItem(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 80,
          child: Text(
            '$label:',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(color: Colors.white, fontSize: 14),
          ),
        ),
      ],
    );
  }

  Widget _buildRecommendationsCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.music_note, color: Colors.white, size: 24),
              const SizedBox(width: 12),
              Text(
                _userProfile != null
                    ? 'Personalized Recommendations'
                    : 'Music Recommendations',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ..._recommendations!
              .map((recommendation) => _buildRecommendationTile(recommendation))
              .toList(),
        ],
      ),
    );
  }

  Widget _buildRecommendationTile(SongRecommendation recommendation) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.1), width: 1),
      ),
      child: Row(
        children: [
          // Album cover
          if (recommendation.albumCover != null)
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                image: DecorationImage(
                  image: NetworkImage(recommendation.albumCover!),
                  fit: BoxFit.cover,
                ),
              ),
            )
          else
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.music_note,
                color: Colors.white,
                size: 24,
              ),
            ),

          const SizedBox(width: 16),

          // Song info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  recommendation.title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  recommendation.artist,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.8),
                    fontSize: 14,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  '${recommendation.popularityString} • ${recommendation.durationString}',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),

          // Play/Open button
          if (recommendation.hasPreview)
            StreamBuilder<PlayerState>(
              stream: _audioService.stateStream,
              builder: (context, snapshot) {
                final isPlaying = _audioService.isPlaying(
                  recommendation.previewUrl!,
                );
                return IconButton(
                  onPressed: () async {
                    if (isPlaying) {
                      await _audioService.stop();
                    } else {
                      await _audioService.play(recommendation.previewUrl!);
                    }
                  },
                  icon: Icon(
                    isPlaying ? Icons.pause : Icons.play_arrow,
                    color: const Color(0xFF1DB954),
                    size: 28,
                  ),
                );
              },
            ),

          // Open in Spotify
          IconButton(
            onPressed: () => _openSpotifyTrack(recommendation.spotifyUrl),
            icon: const Icon(Icons.open_in_new, color: Colors.white, size: 20),
            tooltip: 'Open in Spotify',
          ),
        ],
      ),
    );
  }
}
