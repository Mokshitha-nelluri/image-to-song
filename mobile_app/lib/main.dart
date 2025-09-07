import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const ImageToSongApp());
}

class ImageToSongApp extends StatelessWidget {
  const ImageToSongApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '🎵 Image-to-Song',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1DB954), // Spotify green
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const LoginScreen(), // Start with login screen
      debugShowCheckedModeBanner: false,
    );
  }
}
