import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'config.dart';

class SpotifyAuthScreen extends StatefulWidget {
  const SpotifyAuthScreen({super.key});

  @override
  State<SpotifyAuthScreen> createState() => _SpotifyAuthScreenState();
}

class _SpotifyAuthScreenState extends State<SpotifyAuthScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _initializeWebView();
  }

  Future<void> _initializeWebView() async {
    try {
      // Get auth URL from backend
      final response = await http.get(
        Uri.parse('${Config.baseUrl}/spotify/login'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final authUrl = data['auth_url'];

        // Initialize WebView
        _controller = WebViewController()
          ..setJavaScriptMode(JavaScriptMode.unrestricted)
          ..setNavigationDelegate(
            NavigationDelegate(
              onPageStarted: (String url) {
                setState(() {
                  _isLoading = true;
                });

                // Check if we've been redirected back to our callback
                if (url.contains('/spotify/callback')) {
                  _handleCallback(url);
                }
              },
              onPageFinished: (String url) {
                setState(() {
                  _isLoading = false;
                });
              },
              onWebResourceError: (WebResourceError error) {
                setState(() {
                  _error = 'Failed to load: ${error.description}';
                  _isLoading = false;
                });
              },
            ),
          )
          ..loadRequest(Uri.parse(authUrl));

        setState(() {
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Failed to get auth URL';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  void _handleCallback(String url) {
    // Check if the URL contains a successful callback
    if (url.contains('code=') || url.contains('?code=')) {
      // Authentication successful
      Navigator.pop(context, true); // Return success
    } else if (url.contains('error=')) {
      // Authentication failed
      Navigator.pop(context, false); // Return failure
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🎵 Connect Spotify'),
        backgroundColor: const Color(0xFF1DB954), // Spotify green
        foregroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context, false),
        ),
      ),
      body: Stack(
        children: [
          if (_error != null)
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(
                    'Authentication Error',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(_error!),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('Close'),
                  ),
                ],
              ),
            )
          else if (_isLoading)
            const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Color(0xFF1DB954)),
                  SizedBox(height: 16),
                  Text('Loading Spotify login...'),
                ],
              ),
            )
          else
            WebViewWidget(controller: _controller),

          // Loading overlay
          if (_isLoading && _error == null)
            Container(
              color: Colors.white.withOpacity(0.8),
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(color: Color(0xFF1DB954)),
                    SizedBox(height: 16),
                    Text('Connecting to Spotify...'),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
