import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config.dart';
import 'screens/welcome_screen.dart';
import 'services/audio_service.dart';

void main() {
  runApp(const ImageToSongApp());
}

class ImageToSongApp extends StatelessWidget {
  const ImageToSongApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Audio service provider for global audio state management
        Provider<AudioService>(
          create: (_) => AudioService(),
          dispose: (_, audioService) => audioService.dispose(),
        ),
      ],
      child: MaterialApp(
        title: AppConfig.appName,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(AppConfig.spotifyGreenPrimary),
            brightness: Brightness.light,
          ),
          useMaterial3: true,
          appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
        ),
        darkTheme: AppConfig.enableDarkMode
            ? ThemeData(
                colorScheme: ColorScheme.fromSeed(
                  seedColor: const Color(AppConfig.spotifyGreenPrimary),
                  brightness: Brightness.dark,
                ),
                useMaterial3: true,
                appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
              )
            : null,
        home: const WelcomeScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
