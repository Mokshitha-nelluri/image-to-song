import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/quiz_song.dart';
import '../models/user_music_profile.dart';
import '../services/api_service.dart';
import '../services/profile_service.dart';
import '../services/audio_service.dart';
import 'quiz_results_screen.dart';

class QuizScreen extends StatefulWidget {
  const QuizScreen({super.key});

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> with TickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  final ProfileService _profileService = ProfileService();
  final AudioService _audioService = AudioService();

  late AnimationController _cardController;
  late AnimationController _progressController;
  late Animation<double> _cardAnimation;
  late Animation<double> _progressAnimation;

  List<QuizSong> _quizSongs = [];
  int _currentIndex = 0;
  bool _isLoading = true;
  String? _error;
  bool _isSwipeInProgress = false;

  // Track user ratings
  final List<Map<String, dynamic>> _songRatings = [];

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _loadQuizSongs();
  }

  void _setupAnimations() {
    _cardController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _progressController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );

    _cardAnimation = Tween<double>(begin: 1.0, end: 0.0).animate(
      CurvedAnimation(parent: _cardController, curve: Curves.easeInOut),
    );

    _progressAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _progressController, curve: Curves.easeInOut),
    );
  }

  Future<void> _loadQuizSongs() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final songs = await _apiService.getQuizSongs(limit: 20);

      setState(() {
        _quizSongs = songs;
        _isLoading = false;
      });

      // Cache songs for offline access
      await _profileService.saveQuizSongs(songs);
    } catch (e) {
      print('Error loading quiz songs: $e');

      // Try to load cached songs
      try {
        final cachedSongs = await _profileService.loadCachedQuizSongs();
        if (cachedSongs != null && cachedSongs.isNotEmpty) {
          setState(() {
            _quizSongs = cachedSongs;
            _isLoading = false;
          });
          return;
        }
      } catch (cacheError) {
        print('Error loading cached songs: $cacheError');
      }

      setState(() {
        _error = 'Failed to load quiz songs. Please check your connection.';
        _isLoading = false;
      });
    }
  }

  Future<void> _rateSong(bool liked) async {
    if (_isSwipeInProgress || _currentIndex >= _quizSongs.length) return;

    setState(() {
      _isSwipeInProgress = true;
    });

    final currentSong = _quizSongs[_currentIndex];
    currentSong.userLiked = liked;
    currentSong.ratedAt = DateTime.now();

    // Add to ratings list
    _songRatings.add({
      'song_id': currentSong.id,
      'liked': liked,
      'rated_at': currentSong.ratedAt!.millisecondsSinceEpoch,
    });

    // Stop audio if playing
    await _audioService.stop();

    // Animate card out
    await _cardController.forward();

    // Update progress
    final progress = (_currentIndex + 1) / _quizSongs.length;
    _progressController.animateTo(progress);

    // Haptic feedback
    HapticFeedback.lightImpact();

    // Move to next song or finish quiz
    if (_currentIndex < _quizSongs.length - 1) {
      // Reset card animation and prepare for next song
      _cardController.reset();

      // Use a small delay to ensure smooth animation
      await Future.delayed(const Duration(milliseconds: 50));

      setState(() {
        _currentIndex++;
        _isSwipeInProgress = false;
      });
    } else {
      // Quiz completed
      await _finishQuiz();
    }
  }

  Future<void> _finishQuiz() async {
    try {
      // Calculate preferences
      final userId = 'user_${DateTime.now().millisecondsSinceEpoch}';

      final userProfile = await _apiService.calculatePreferences(
        userId: userId,
        songRatings: _songRatings,
      );

      // Save profile locally
      await _profileService.saveProfile(userProfile);

      // Navigate to results
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => QuizResultsScreen(
              userProfile: userProfile,
              ratedSongs: _quizSongs.where((song) => song.isRated).toList(),
            ),
          ),
        );
      }
    } catch (e) {
      print('Error finishing quiz: $e');

      // Fallback: Save basic profile
      try {
        final basicProfile = _createBasicProfile();
        await _profileService.saveProfile(basicProfile);

        if (mounted) {
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
              builder: (context) => QuizResultsScreen(
                userProfile: basicProfile,
                ratedSongs: _quizSongs.where((song) => song.isRated).toList(),
              ),
            ),
          );
        }
      } catch (fallbackError) {
        print('Error with fallback profile: $fallbackError');
        _showErrorDialog('Failed to save your preferences. Please try again.');
      }
    }
  }

  UserMusicProfile _createBasicProfile() {
    final likedSongs = _quizSongs
        .where((song) => song.userLiked == true)
        .toList();
    final dislikedSongs = _quizSongs
        .where((song) => song.userLiked == false)
        .toList();

    // Simple genre preference calculation
    final genrePreferences = <String, double>{};
    for (final song in likedSongs) {
      for (final genre in song.genres) {
        genrePreferences[genre] = (genrePreferences[genre] ?? 0) + 1;
      }
    }

    // Normalize
    final maxCount = genrePreferences.values.isNotEmpty
        ? genrePreferences.values.reduce((a, b) => a > b ? a : b)
        : 1.0;

    genrePreferences.updateAll((key, value) => value / maxCount);

    // Basic audio features (simplified)
    final audioFeaturePreferences = <String, double>{
      'danceability': 0.5,
      'energy': 0.5,
      'valence': 0.5,
      'acousticness': 0.5,
      'instrumentalness': 0.1,
    };

    return UserMusicProfile(
      userId: 'user_${DateTime.now().millisecondsSinceEpoch}',
      createdAt: DateTime.now(),
      lastUpdated: DateTime.now(),
      quizCompleted: true,
      genrePreferences: genrePreferences,
      audioFeaturePreferences: audioFeaturePreferences,
      likedArtists: likedSongs.map((song) => song.artist).toSet().toList(),
      dislikedArtists: dislikedSongs
          .map((song) => song.artist)
          .toSet()
          .toList(),
      likedTrackIds: likedSongs.map((song) => song.id).toList(),
      dislikedTrackIds: dislikedSongs.map((song) => song.id).toList(),
      totalSongsRated: _songRatings.length,
      songsLiked: likedSongs.length,
      songsDisliked: dislikedSongs.length,
      completionRate: _songRatings.length / _quizSongs.length,
    );
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Error'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              Navigator.of(context).pop(); // Go back to welcome
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Future<void> _toggleAudio() async {
    if (_currentIndex >= _quizSongs.length) return;

    final currentSong = _quizSongs[_currentIndex];

    if (!currentSong.hasPreview) {
      _showNoPreviewSnackBar();
      return;
    }

    try {
      if (_audioService.isPlaying(currentSong.previewUrl!)) {
        await _audioService.pause();
      } else if (_audioService.isPaused(currentSong.previewUrl!)) {
        await _audioService.resume();
      } else {
        await _audioService.play(currentSong.previewUrl!);
      }
    } catch (e) {
      print('Audio error: $e');
      _showNoPreviewSnackBar();
    }
  }

  void _showNoPreviewSnackBar() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Preview not available for this song'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  void dispose() {
    _cardController.dispose();
    _progressController.dispose();
    _audioService.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF191414), // Spotify dark
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text(
          'Music Quiz',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        centerTitle: true,
      ),
      body: _isLoading
          ? _buildLoadingView()
          : _error != null
          ? _buildErrorView()
          : _buildQuizView(),
    );
  }

  Widget _buildLoadingView() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF1DB954)),
          ),
          SizedBox(height: 24),
          Text(
            'Loading your music quiz...',
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 64),
            const SizedBox(height: 24),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontSize: 16),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _loadQuizSongs,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1DB954),
                foregroundColor: Colors.white,
              ),
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuizView() {
    if (_quizSongs.isEmpty) {
      return const Center(
        child: Text(
          'No quiz songs available',
          style: TextStyle(color: Colors.white),
        ),
      );
    }

    return Column(
      children: [
        // Progress bar
        _buildProgressBar(),

        // Quiz instructions
        _buildInstructions(),

        // Song card
        Expanded(child: _buildSongCard()),

        // Action buttons
        Padding(
          padding: const EdgeInsets.only(top: 20.0, bottom: 8.0),
          child: _buildActionButtons(),
        ),

        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildProgressBar() {
    final progress = _currentIndex / _quizSongs.length;

    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Song ${_currentIndex + 1} of ${_quizSongs.length}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                '${(progress * 100).round()}%',
                style: const TextStyle(
                  color: Color(0xFF1DB954),
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: progress,
            backgroundColor: Colors.white.withOpacity(0.2),
            valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF1DB954)),
            minHeight: 4,
          ),
        ],
      ),
    );
  }

  Widget _buildInstructions() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: const Row(
        children: [
          Icon(Icons.swipe, color: Colors.white, size: 20),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Tap ❤️ if you like it, ✕ if you don\'t. Listen to previews first!',
              style: TextStyle(color: Colors.white, fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSongCard() {
    if (_currentIndex >= _quizSongs.length) {
      return const SizedBox.shrink();
    }

    final song = _quizSongs[_currentIndex];

    return AnimatedBuilder(
      animation: _cardAnimation,
      builder: (context, child) {
        // Only apply animation when actually animating out
        final animationValue = _isSwipeInProgress ? _cardAnimation.value : 0.0;

        return Transform.scale(
          scale: 1.0 - (animationValue * 0.1),
          child: Opacity(
            opacity: 1.0 - animationValue,
            child: Container(
              margin: const EdgeInsets.all(24.0),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Album cover
                  Container(
                    width: 200,
                    height: 200,
                    margin: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      image: DecorationImage(
                        image: NetworkImage(song.albumCover),
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),

                  // Song info
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24.0),
                    child: Column(
                      children: [
                        Text(
                          song.title,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.black,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          song.artist,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 18,
                            color: Colors.grey[600],
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          song.genresString,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[500],
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Play button
                  StreamBuilder<PlayerState>(
                    stream: _audioService.stateStream,
                    builder: (context, snapshot) {
                      final isPlaying = _audioService.isPlaying(
                        song.previewUrl ?? '',
                      );
                      final isPaused = _audioService.isPaused(
                        song.previewUrl ?? '',
                      );
                      final isLoading = _audioService.isLoading(
                        song.previewUrl ?? '',
                      );

                      return Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          color: song.hasPreview
                              ? const Color(0xFF1DB954)
                              : Colors.grey,
                          borderRadius: BorderRadius.circular(40),
                          boxShadow: [
                            BoxShadow(
                              color:
                                  (song.hasPreview
                                          ? const Color(0xFF1DB954)
                                          : Colors.grey)
                                      .withOpacity(0.3),
                              blurRadius: 12,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: IconButton(
                          onPressed: song.hasPreview ? _toggleAudio : null,
                          icon: Icon(
                            isLoading
                                ? Icons.hourglass_empty
                                : isPlaying
                                ? Icons.pause
                                : isPaused
                                ? Icons.play_arrow
                                : Icons.play_arrow,
                            color: Colors.white,
                            size: 36,
                          ),
                        ),
                      );
                    },
                  ),

                  const SizedBox(height: 16),

                  Text(
                    song.hasPreview
                        ? 'Tap to play 30s preview'
                        : 'Preview not available',
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  ),

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildActionButtons() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 48.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // Dislike button
          Container(
            width: 70,
            height: 70,
            decoration: BoxDecoration(
              color: Colors.red.withOpacity(0.1),
              borderRadius: BorderRadius.circular(35),
              border: Border.all(color: Colors.red, width: 2),
            ),
            child: IconButton(
              onPressed: _isSwipeInProgress ? null : () => _rateSong(false),
              icon: const Icon(Icons.close, color: Colors.red, size: 32),
            ),
          ),

          // Like button
          Container(
            width: 70,
            height: 70,
            decoration: BoxDecoration(
              color: const Color(0xFF1DB954).withOpacity(0.1),
              borderRadius: BorderRadius.circular(35),
              border: Border.all(color: const Color(0xFF1DB954), width: 2),
            ),
            child: IconButton(
              onPressed: _isSwipeInProgress ? null : () => _rateSong(true),
              icon: const Icon(
                Icons.favorite,
                color: Color(0xFF1DB954),
                size: 32,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
