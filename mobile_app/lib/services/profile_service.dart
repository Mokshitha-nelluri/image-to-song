import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../config.dart';
import '../models/user_music_profile.dart';
import '../models/quiz_song.dart';

class ProfileService {
  static const String _profileKey = AppConfig.userProfileKey;
  static const String _quizCompletedKey = AppConfig.quizCompletedKey;
  static const String _quizSongsKey = AppConfig.quizSongsKey;
  static const String _appVersionKey = AppConfig.appVersionKey;

  static const String currentAppVersion = AppConfig.appVersion;

  // Save user music profile
  Future<void> saveProfile(UserMusicProfile profile) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final profileJson = json.encode(profile.toJson());

      await prefs.setString(_profileKey, profileJson);
      await prefs.setBool(_quizCompletedKey, profile.quizCompleted);
      await prefs.setString(_appVersionKey, currentAppVersion);

      print('✅ Profile saved successfully');
    } catch (e) {
      print('❌ Failed to save profile: $e');
      throw Exception('Failed to save profile: $e');
    }
  }

  // Load user music profile
  Future<UserMusicProfile?> loadProfile() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final profileJson = prefs.getString(_profileKey);

      if (profileJson != null) {
        final profileData = json.decode(profileJson);
        return UserMusicProfile.fromJson(profileData);
      }

      return null;
    } catch (e) {
      print('❌ Failed to load profile: $e');
      return null;
    }
  }

  // Check if quiz is completed
  Future<bool> isQuizCompleted() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool(_quizCompletedKey) ?? false;
    } catch (e) {
      print('❌ Failed to check quiz status: $e');
      return false;
    }
  }

  // Save quiz songs (for offline access)
  Future<void> saveQuizSongs(List<QuizSong> songs) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final songsJson = json.encode(
        songs.map((song) => song.toJson()).toList(),
      );

      await prefs.setString(_quizSongsKey, songsJson);
      print('✅ Quiz songs cached successfully');
    } catch (e) {
      print('❌ Failed to cache quiz songs: $e');
    }
  }

  // Load cached quiz songs
  Future<List<QuizSong>?> loadCachedQuizSongs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final songsJson = prefs.getString(_quizSongsKey);

      if (songsJson != null) {
        final List<dynamic> songsData = json.decode(songsJson);
        return songsData
            .map((songData) => QuizSong.fromJson(songData))
            .toList();
      }

      return null;
    } catch (e) {
      print('❌ Failed to load cached quiz songs: $e');
      return null;
    }
  }

  // Update profile with new quiz results
  Future<UserMusicProfile> updateProfileWithQuizResults(
    UserMusicProfile profile,
    List<QuizSong> ratedSongs,
  ) async {
    final likedSongs = ratedSongs
        .where((song) => song.userLiked == true)
        .toList();
    final dislikedSongs = ratedSongs
        .where((song) => song.userLiked == false)
        .toList();

    final updatedProfile = profile.copyWith(
      lastUpdated: DateTime.now(),
      quizCompleted: true,
      totalSongsRated: ratedSongs.length,
      songsLiked: likedSongs.length,
      songsDisliked: dislikedSongs.length,
      completionRate: ratedSongs.length / 20.0, // Assuming 20 total songs
      likedArtists: likedSongs.map((song) => song.artist).toSet().toList(),
      dislikedArtists: dislikedSongs
          .map((song) => song.artist)
          .toSet()
          .toList(),
      likedTrackIds: likedSongs.map((song) => song.id).toList(),
      dislikedTrackIds: dislikedSongs.map((song) => song.id).toList(),
    );

    await saveProfile(updatedProfile);
    return updatedProfile;
  }

  // Export user data (for privacy compliance)
  Future<Map<String, dynamic>> exportUserData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final profile = await loadProfile();
      final quizSongs = await loadCachedQuizSongs();

      return {
        'profile': profile?.toJson(),
        'quiz_songs': quizSongs?.map((song) => song.toJson()).toList(),
        'app_version': prefs.getString(_appVersionKey),
        'export_date': DateTime.now().toIso8601String(),
      };
    } catch (e) {
      throw Exception('Failed to export user data: $e');
    }
  }

  // Delete all user data (for privacy compliance)
  Future<void> deleteAllUserData() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      await prefs.remove(_profileKey);
      await prefs.remove(_quizCompletedKey);
      await prefs.remove(_quizSongsKey);
      await prefs.remove(_appVersionKey);

      print('✅ All user data deleted successfully');
    } catch (e) {
      print('❌ Failed to delete user data: $e');
      throw Exception('Failed to delete user data: $e');
    }
  }

  // Check if app was updated (for migration handling)
  Future<bool> isAppUpdated() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedVersion = prefs.getString(_appVersionKey);

      return savedVersion != null && savedVersion != currentAppVersion;
    } catch (e) {
      return false;
    }
  }

  // Get app statistics
  Future<Map<String, dynamic>> getAppStatistics() async {
    try {
      final profile = await loadProfile();
      final isCompleted = await isQuizCompleted();
      final cachedSongs = await loadCachedQuizSongs();

      return {
        'has_profile': profile != null,
        'quiz_completed': isCompleted,
        'cached_songs_count': cachedSongs?.length ?? 0,
        'profile_created_days_ago': profile != null
            ? DateTime.now().difference(profile.createdAt).inDays
            : null,
        'last_updated_days_ago': profile != null
            ? DateTime.now().difference(profile.lastUpdated).inDays
            : null,
      };
    } catch (e) {
      return {'error': e.toString()};
    }
  }
}
