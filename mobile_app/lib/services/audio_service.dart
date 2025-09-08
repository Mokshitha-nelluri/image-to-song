import 'dart:async';

enum PlayerState { playing, paused, stopped, loading, error }

class AudioService {
  static final AudioService _instance = AudioService._internal();
  factory AudioService() => _instance;
  AudioService._internal();

  // For now, we'll create a simple service that tracks state
  // In production, this would use the audioplayers package

  PlayerState _state = PlayerState.stopped;
  String? _currentUrl;
  Duration _position = Duration.zero;
  Duration _duration = const Duration(seconds: 30); // Default preview length

  final StreamController<PlayerState> _stateController =
      StreamController<PlayerState>.broadcast();
  final StreamController<Duration> _positionController =
      StreamController<Duration>.broadcast();

  Timer? _positionTimer;

  // Getters
  PlayerState get state => _state;
  String? get currentUrl => _currentUrl;
  Duration get position => _position;
  Duration get duration => _duration;

  // Streams
  Stream<PlayerState> get stateStream => _stateController.stream;
  Stream<Duration> get positionStream => _positionController.stream;

  // Play a song preview
  Future<void> play(String url) async {
    try {
      // Stop current playback if any
      await stop();

      _currentUrl = url;
      _state = PlayerState.loading;
      _stateController.add(_state);

      print('🎵 Playing preview: $url');

      // Simulate loading time
      await Future.delayed(const Duration(milliseconds: 500));

      _state = PlayerState.playing;
      _position = Duration.zero;
      _stateController.add(_state);
      _positionController.add(_position);

      // Start position timer
      _startPositionTimer();

      // Auto-stop after 30 seconds (preview length)
      Timer(const Duration(seconds: 30), () {
        if (_state == PlayerState.playing && _currentUrl == url) {
          stop();
        }
      });
    } catch (e) {
      print('❌ Audio playback error: $e');
      _state = PlayerState.error;
      _stateController.add(_state);
      throw Exception('Failed to play audio: $e');
    }
  }

  // Pause playback
  Future<void> pause() async {
    if (_state == PlayerState.playing) {
      _state = PlayerState.paused;
      _stateController.add(_state);
      _stopPositionTimer();

      print('⏸️ Audio paused');
    }
  }

  // Resume playback
  Future<void> resume() async {
    if (_state == PlayerState.paused) {
      _state = PlayerState.playing;
      _stateController.add(_state);
      _startPositionTimer();

      print('▶️ Audio resumed');
    }
  }

  // Stop playback
  Future<void> stop() async {
    if (_state != PlayerState.stopped) {
      _state = PlayerState.stopped;
      _currentUrl = null;
      _position = Duration.zero;

      _stateController.add(_state);
      _positionController.add(_position);
      _stopPositionTimer();

      print('⏹️ Audio stopped');
    }
  }

  // Toggle play/pause
  Future<void> togglePlayPause() async {
    if (_state == PlayerState.playing) {
      await pause();
    } else if (_state == PlayerState.paused) {
      await resume();
    }
  }

  // Seek to position
  Future<void> seek(Duration position) async {
    if (position <= _duration) {
      _position = position;
      _positionController.add(_position);

      print('⏭️ Seeking to: ${position.inSeconds}s');
    }
  }

  // Check if a specific URL is currently playing
  bool isPlaying(String url) {
    return _currentUrl == url && _state == PlayerState.playing;
  }

  // Check if a specific URL is currently paused
  bool isPaused(String url) {
    return _currentUrl == url && _state == PlayerState.paused;
  }

  // Check if a specific URL is currently loading
  bool isLoading(String url) {
    return _currentUrl == url && _state == PlayerState.loading;
  }

  // Get progress as percentage (0.0 to 1.0)
  double get progress {
    if (_duration.inMilliseconds == 0) return 0.0;
    return _position.inMilliseconds / _duration.inMilliseconds;
  }

  // Format duration for display
  String formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }

  void _startPositionTimer() {
    _stopPositionTimer();
    _positionTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) {
      if (_state == PlayerState.playing) {
        _position = Duration(milliseconds: _position.inMilliseconds + 100);
        _positionController.add(_position);

        // Stop at end of preview
        if (_position >= _duration) {
          stop();
        }
      }
    });
  }

  void _stopPositionTimer() {
    _positionTimer?.cancel();
    _positionTimer = null;
  }

  // Dispose resources
  void dispose() {
    _stopPositionTimer();
    _stateController.close();
    _positionController.close();
  }
}

// Simple audio service manager
class AudioServiceManager {
  static final AudioService _instance = AudioService._internal();
  static AudioService get instance => _instance;
}

// Simple audio service for fallback when audioplayers is not available
class SimpleAudioService {
  static Future<void> playUrl(String url) async {
    print('🎵 [SIMPLE] Would play: $url');
    // In a real implementation, this might open the URL in a browser
    // or show a message to the user about audio not being supported
  }
}
