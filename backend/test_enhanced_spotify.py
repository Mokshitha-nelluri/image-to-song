"""
Enhanced Spotify Integration Test
Tests the improved mood analysis and music recommendation pipeline.
"""

import asyncio
import json
import time
from pathlib import Path

# Mock data for testing without Spotify credentials
def test_enhanced_mood_analysis():
    """Test the enhanced mood analysis pipeline."""
    
    # Import our enhanced mood analyzer
    import sys
    sys.path.append(str(Path(__file__).parent / "app"))
    
    from app.services.enhanced_mood_service import enhanced_mood_analyzer
    
    # Test cases with different image scenarios
    test_cases = [
        {
            "name": "Happy Beach Photo",
            "caption": "a sunny beach with blue water and people playing volleyball",
            "dominant_colors": [
                {"rgb": (255, 255, 0), "percentage": 35},  # Yellow (sun/sand)
                {"rgb": (0, 150, 255), "percentage": 40},  # Blue (water)
                {"rgb": (255, 200, 150), "percentage": 25} # Orange (sunset)
            ]
        },
        {
            "name": "Peaceful Forest",
            "caption": "a quiet forest path with tall trees and morning mist",
            "dominant_colors": [
                {"rgb": (34, 139, 34), "percentage": 60},   # Forest green
                {"rgb": (139, 69, 19), "percentage": 25},   # Brown (trees)
                {"rgb": (200, 200, 200), "percentage": 15}  # Light gray (mist)
            ]
        },
        {
            "name": "Rainy City Night",
            "caption": "a dark street at night with rain and street lights",
            "dominant_colors": [
                {"rgb": (25, 25, 25), "percentage": 50},    # Dark gray/black
                {"rgb": (100, 100, 120), "percentage": 30}, # Blue-gray
                {"rgb": (255, 255, 100), "percentage": 20}  # Yellow (lights)
            ]
        },
        {
            "name": "Energetic Sports",
            "caption": "people playing basketball in a bright gym with energy and action",
            "dominant_colors": [
                {"rgb": (255, 0, 0), "percentage": 40},     # Red (energy)
                {"rgb": (255, 165, 0), "percentage": 35},   # Orange (basketball)
                {"rgb": (255, 255, 255), "percentage": 25}  # White (gym)
            ]
        },
        {
            "name": "Romantic Sunset",
            "caption": "a couple holding hands watching a beautiful sunset by the ocean",
            "dominant_colors": [
                {"rgb": (255, 20, 147), "percentage": 30},  # Deep pink
                {"rgb": (255, 140, 0), "percentage": 40},   # Orange (sunset)
                {"rgb": (70, 130, 180), "percentage": 30}   # Steel blue (ocean)
            ]
        }
    ]
    
    print("🎵 Enhanced Spotify Integration Test Results\n")
    print("="*60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Caption: {test_case['caption']}")
        
        # Create mood analysis input
        mood_analysis = {
            "caption": test_case["caption"],
            "dominant_colors": test_case["dominant_colors"],
            "image_info": {"format": "JPEG", "size": (1024, 768)}
        }
        
        # Run enhanced mood analysis
        start_time = time.time()
        enhanced_result = enhanced_mood_analyzer.analyze_comprehensive_mood(mood_analysis)
        analysis_time = time.time() - start_time
        
        # Display results
        print(f"   🎯 Primary Mood: {enhanced_result['primary_mood']} (confidence: {enhanced_result['mood_confidence']:.2f})")
        print(f"   📊 Audio Features:")
        audio_features = enhanced_result["audio_features"]
        print(f"      • Valence (happiness): {audio_features['valence']:.2f}")
        print(f"      • Energy: {audio_features['energy']:.2f}")
        print(f"      • Danceability: {audio_features['danceability']:.2f}")
        print(f"      • Acousticness: {audio_features['acousticness']:.2f}")
        print(f"      • Tempo: {audio_features['tempo']:.0f} BPM")
        
        print(f"   🎼 Recommended Genres: {', '.join(enhanced_result['recommended_genres'][:3])}")
        print(f"   💭 Explanation: {enhanced_result['mood_explanation']}")
        print(f"   ⚡ Analysis Time: {analysis_time:.3f}s")
        
        # Show mood breakdown
        breakdown = enhanced_result["mood_breakdown"]
        print(f"   📈 Mood Sources:")
        print(f"      • Text Analysis: {breakdown['text_analysis']['primary_mood']} (conf: {breakdown['text_analysis']['confidence']:.2f})")
        print(f"      • Color Analysis: {breakdown['color_analysis']['primary_mood']} (conf: {breakdown['color_analysis']['confidence']:.2f})")
        print(f"      • Scene Analysis: {breakdown['scene_analysis']['primary_mood']} (conf: {breakdown['scene_analysis']['confidence']:.2f})")
        
        print("   " + "-"*50)

    print(f"\n✅ Enhanced mood analysis test completed!")
    print(f"🚀 Ready for Spotify integration with detailed mood understanding!")

def simulate_spotify_recommendations():
    """Simulate what Spotify recommendations would look like."""
    
    print("\n" + "="*60)
    print("🎵 SIMULATED SPOTIFY RECOMMENDATIONS")
    print("="*60)
    
    # Simulated Spotify response for different moods
    mood_examples = {
        "happy": [
            {"name": "Good as Hell", "artist": "Lizzo", "genre": "Pop"},
            {"name": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "genre": "Funk"},
            {"name": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "genre": "Pop"},
        ],
        "peaceful": [
            {"name": "Weightless", "artist": "Marconi Union", "genre": "Ambient"},
            {"name": "River", "artist": "Joni Mitchell", "genre": "Folk"},
            {"name": "Claire de Lune", "artist": "Claude Debussy", "genre": "Classical"},
        ],
        "melancholic": [
            {"name": "Mad World", "artist": "Gary Jules", "genre": "Alternative"},
            {"name": "The Sound of Silence", "artist": "Simon & Garfunkel", "genre": "Folk"},
            {"name": "Hurt", "artist": "Johnny Cash", "genre": "Country"},
        ],
        "energetic": [
            {"name": "Pump It", "artist": "The Black Eyed Peas", "genre": "Hip-Hop"},
            {"name": "Thunder", "artist": "Imagine Dragons", "genre": "Rock"},
            {"name": "Bangarang", "artist": "Skrillex", "genre": "Electronic"},
        ]
    }
    
    for mood, tracks in mood_examples.items():
        print(f"\n🎵 {mood.upper()} MOOD RECOMMENDATIONS:")
        for track in tracks:
            print(f"   ♪ {track['name']} - {track['artist']} ({track['genre']})")
    
    print(f"\n💡 The enhanced pipeline would provide:")
    print(f"   • 10+ personalized recommendations per mood")
    print(f"   • Genre-specific recommendations")
    print(f"   • User's listening history integration")
    print(f"   • Audio feature matching (valence, energy, etc.)")
    print(f"   • Real Spotify playback links")

if __name__ == "__main__":
    print("🎵 Starting Enhanced Spotify Integration Tests...")
    test_enhanced_mood_analysis()
    simulate_spotify_recommendations()
    
    print(f"\n" + "="*60)
    print("🎯 NEXT STEPS TO COMPLETE INTEGRATION:")
    print("="*60)
    print("1. ✅ Enhanced mood analysis - COMPLETED")
    print("2. ✅ Advanced audio feature mapping - COMPLETED") 
    print("3. ✅ Multi-layer mood detection - COMPLETED")
    print("4. 🔄 Set up Spotify Developer Account - PENDING")
    print("5. 🔄 Add Spotify credentials to .env - PENDING")
    print("6. 🔄 Test with real Spotify API - PENDING")
    print("7. 🔄 Mobile app integration - PENDING")
    
    print(f"\n🚀 The enhanced pipeline is ready!")
    print(f"📱 Time to focus on mobile app development!")
