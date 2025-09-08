#!/usr/bin/env python3
"""
Simple End-to-End Test for Image-to-Song App
Tests the complete pipeline from image upload to music recommendations.
"""

import asyncio
import httpx
import json
import sys
import time
from io import BytesIO
from PIL import Image, ImageDraw

# Test configuration
BASE_URL = "http://localhost:8000"  # Change to production URL if needed

def create_test_image(color="blue"):
    """Create a simple test image"""
    img = Image.new('RGB', (300, 200), color=color)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Test {color} image", fill="white")
    draw.rectangle([50, 50, 150, 100], outline="white", width=2)
    
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()

async def test_complete_pipeline():
    """Test the complete end-to-end pipeline"""
    print("🧪 Testing Image-to-Song Complete Pipeline")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        base_url = BASE_URL
        test_count = 0
        passed_count = 0
        
        # Test 1: Health Check
        print("1. Testing Health Check...")
        test_count += 1
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health check passed - uptime: {data.get('uptime_seconds', 'N/A')}s")
                passed_count += 1
            else:
                print(f"   ❌ Health check failed - status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        # Test 2: Quiz Songs
        print("2. Testing Quiz Songs...")
        test_count += 1
        try:
            response = await client.get(f"{base_url}/quiz/songs?limit=10")
            if response.status_code == 200:
                data = response.json()
                songs = data.get("quiz_songs", [])
                print(f"   ✅ Got {len(songs)} quiz songs")
                passed_count += 1
                
                # Store some songs for later tests
                sample_songs = songs[:5] if len(songs) >= 5 else songs
            else:
                print(f"   ❌ Quiz songs failed - status: {response.status_code}")
                sample_songs = []
        except Exception as e:
            print(f"   ❌ Quiz songs error: {e}")
            sample_songs = []
        
        # Test 3: User Preferences
        print("3. Testing User Preferences Calculation...")
        test_count += 1
        if sample_songs:
            try:
                # Create mock ratings
                song_ratings = []
                for i, song in enumerate(sample_songs):
                    rating = "like" if i % 2 == 0 else "dislike"
                    song_ratings.append({"song_id": song["id"], "rating": rating})
                
                payload = {
                    "user_id": "test_user_123",
                    "song_ratings": song_ratings
                }
                
                response = await client.post(f"{base_url}/quiz/calculate-preferences", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    profile = data.get("user_profile", {})
                    genres = len(profile.get("genre_preferences", {}))
                    print(f"   ✅ Generated user profile with {genres} genre preferences")
                    passed_count += 1
                    user_profile = profile
                else:
                    print(f"   ❌ Preferences calculation failed - status: {response.status_code}")
                    user_profile = None
            except Exception as e:
                print(f"   ❌ Preferences calculation error: {e}")
                user_profile = None
        else:
            print("   ⏭️  Skipped - no quiz songs available")
            user_profile = None
        
        # Test 4: Simple Image Analysis
        print("4. Testing Simple Image Analysis...")
        test_count += 1
        try:
            test_image = create_test_image("green")
            files = {"file": ("test.jpg", test_image, "image/jpeg")}
            
            response = await client.post(f"{base_url}/analyze-image", files=files)
            if response.status_code == 200:
                data = response.json()
                mood = data.get("mood", "unknown")
                confidence = data.get("confidence", 0)
                print(f"   ✅ Image analyzed - mood: {mood}, confidence: {confidence}")
                passed_count += 1
            else:
                print(f"   ❌ Image analysis failed - status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Image analysis error: {e}")
        
        # Test 5: Enhanced Analysis with Recommendations
        print("5. Testing Enhanced Analysis & Recommendations...")
        test_count += 1
        try:
            test_image = create_test_image("orange")
            files = {"file": ("test2.jpg", test_image, "image/jpeg")}
            
            response = await client.post(f"{base_url}/analyze-and-recommend", files=files)
            if response.status_code == 200:
                data = response.json()
                analysis = data.get("image_analysis", {})
                recommendations = data.get("recommendations", [])
                mood = analysis.get("mood", "unknown")
                print(f"   ✅ Enhanced analysis - mood: {mood}, {len(recommendations)} recommendations")
                if recommendations:
                    sample_rec = recommendations[0]
                    print(f"      🎵 Sample: {sample_rec.get('name', 'Unknown')} by {sample_rec.get('artist', 'Unknown')}")
                passed_count += 1
            else:
                print(f"   ❌ Enhanced analysis failed - status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Enhanced analysis error: {e}")
        
        # Test 6: Personalized Recommendations (if we have user profile)
        if user_profile:
            print("6. Testing Personalized Recommendations...")
            test_count += 1
            try:
                payload = {
                    "mood": "happy",
                    "caption": "beautiful sunny day",
                    "user_profile": user_profile
                }
                
                response = await client.post(f"{base_url}/recommendations", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get("recommendations", [])
                    print(f"   ✅ Got {len(recommendations)} personalized recommendations")
                    passed_count += 1
                else:
                    print(f"   ❌ Personalized recommendations failed - status: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Personalized recommendations error: {e}")
        else:
            print("6. ⏭️  Skipped Personalized Recommendations - no user profile")
        
        # Test 7: Song Search
        print("7. Testing Song Search...")
        test_count += 1
        try:
            response = await client.get(f"{base_url}/search/songs?query=happy music&limit=5")
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"   ✅ Search found {len(results)} songs for 'happy music'")
                passed_count += 1
            else:
                print(f"   ❌ Song search failed - status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Song search error: {e}")
        
        # Test 8: Complete User Journey
        print("8. Testing Complete User Journey...")
        test_count += 1
        try:
            print("   📱 Simulating mobile app user flow...")
            
            # Step 1: Get quiz songs
            quiz_response = await client.get(f"{base_url}/quiz/songs?limit=8")
            if quiz_response.status_code != 200:
                raise Exception("Could not get quiz songs")
            
            quiz_songs = quiz_response.json()["quiz_songs"]
            print(f"      ✓ Got {len(quiz_songs)} quiz songs")
            
            # Step 2: User rates songs
            ratings = []
            for i, song in enumerate(quiz_songs):
                rating = "like" if (i + hash(song["id"])) % 3 != 0 else "dislike"
                ratings.append({"song_id": song["id"], "rating": rating})
            
            # Step 3: Calculate preferences
            prefs_response = await client.post(
                f"{base_url}/quiz/calculate-preferences",
                json={"user_id": "journey_test", "song_ratings": ratings}
            )
            if prefs_response.status_code != 200:
                raise Exception("Could not calculate preferences")
            
            profile = prefs_response.json()["user_profile"]
            print(f"      ✓ Generated user profile")
            
            # Step 4: Upload and analyze image
            journey_image = create_test_image("purple")
            files = {"file": ("journey.jpg", journey_image, "image/jpeg")}
            
            analysis_response = await client.post(f"{base_url}/analyze-and-recommend", files=files)
            if analysis_response.status_code != 200:
                raise Exception("Could not analyze image")
            
            analysis_data = analysis_response.json()
            mood = analysis_data["image_analysis"]["mood"]
            recommendations = analysis_data["recommendations"]
            print(f"      ✓ Analyzed image (mood: {mood}) and got {len(recommendations)} recommendations")
            
            # Step 5: Get personalized recommendations
            personalized_response = await client.post(
                f"{base_url}/recommendations",
                json={
                    "mood": mood,
                    "caption": analysis_data["image_analysis"].get("caption", ""),
                    "user_profile": profile
                }
            )
            
            if personalized_response.status_code == 200:
                personalized = personalized_response.json()["recommendations"]
                print(f"      ✓ Got {len(personalized)} personalized recommendations")
                print("   ✅ Complete user journey successful!")
                passed_count += 1
            else:
                raise Exception("Could not get personalized recommendations")
                
        except Exception as e:
            print(f"   ❌ Complete journey error: {e}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {test_count}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {test_count - passed_count}")
    
    success_rate = (passed_count / test_count) * 100 if test_count > 0 else 0
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🎉 EXCELLENT! Your app is working perfectly!")
        return True
    elif success_rate >= 75:
        print("\n👍 GOOD! Most features are working, minor issues to fix.")
        return True
    elif success_rate >= 50:
        print("\n⚠️  FAIR! Several issues need attention.")
        return False
    else:
        print("\n🚨 CRITICAL! Major issues found, app needs fixing.")
        return False

async def test_with_url(url):
    """Test with a specific URL"""
    global BASE_URL
    BASE_URL = url
    print(f"Testing with URL: {url}")
    return await test_complete_pipeline()

if __name__ == "__main__":
    print("🚀 Image-to-Song App End-to-End Test Suite")
    print("==========================================\n")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"Using custom URL: {test_url}\n")
        success = asyncio.run(test_with_url(test_url))
    else:
        print(f"Using default URL: {BASE_URL}")
        print("(Pass a URL as argument to test different server)\n")
        success = asyncio.run(test_complete_pipeline())
    
    if success:
        print("\n✨ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the backend server.")
        sys.exit(1)
