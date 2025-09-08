#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Image-to-Song App
Tests the complete pipeline from image upload to music recommendations.
"""

import asyncio
import httpx
import json
import base64
import os
import sys
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Test configuration
BASE_URL = "http://localhost:8000"  # Change to production URL if needed
TIMEOUT = 30.0

# Test results storage
test_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log_test(test_name: str, status: str, details: str = ""):
    """Log test results"""
    test_results["total_tests"] += 1
    
    if status == "PASS":
        test_results["passed"] += 1
        print(f"✅ {test_name}: {status}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{test_name}: {details}")
        print(f"❌ {test_name}: {status} - {details}")
    
    if details and status == "PASS":
        print(f"   ℹ️  {details}")

def create_test_image(width: int = 300, height: int = 200, color: str = "blue") -> bytes:
    """Create a test image for testing"""
    # Create a simple colored image with text
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    # Add some text to make it more realistic
    try:
        # Try to use default font, fallback to basic if not available
        font = ImageFont.load_default()
    except:
        font = None
    
    text = f"Test {color} image"
    if font:
        draw.text((10, 10), text, fill="white", font=font)
    else:
        draw.text((10, 10), text, fill="white")
    
    # Add some shapes to make it more complex
    draw.rectangle([50, 50, 150, 100], outline="white", width=2)
    draw.ellipse([200, 50, 250, 100], fill="white")
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()

class EndToEndTester:
    """Complete end-to-end test suite"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.user_id = "test_user_123"
        self.user_profile = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def test_health_check(self) -> bool:
        """Test 1: Basic health check"""
        if not self.client:
            log_test("Health Check", "ERROR", "HTTP client not initialized")
            return False
            
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                log_test("Health Check", "PASS", f"Server is healthy, uptime: {data.get('uptime_seconds', 'N/A')}s")
                return True
            else:
                log_test("Health Check", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            log_test("Health Check", "ERROR", str(e))
            return False
    
    async def test_quiz_songs_endpoint(self) -> bool:
        """Test 2: Quiz songs retrieval"""
        if not self.client:
            log_test("Quiz Songs", "ERROR", "HTTP client not initialized")
            return False
            
        try:
            response = await self.client.get(f"{self.base_url}/quiz/songs?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                songs = data.get("quiz_songs", [])
                
                if len(songs) >= 10:
                    # Validate song structure
                    first_song = songs[0]
                    required_fields = ["id", "name", "artist", "genres", "audio_features"]
                    
                    missing_fields = [field for field in required_fields if field not in first_song]
                    
                    if not missing_fields:
                        log_test("Quiz Songs", "PASS", f"Retrieved {len(songs)} songs with correct structure")
                        return True
                    else:
                        log_test("Quiz Songs", "FAIL", f"Missing fields: {missing_fields}")
                        return False
                else:
                    log_test("Quiz Songs", "FAIL", f"Expected at least 10 songs, got {len(songs)}")
                    return False
            else:
                log_test("Quiz Songs", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            log_test("Quiz Songs", "ERROR", str(e))
            return False
    
    async def test_preferences_calculation(self) -> bool:
        """Test 3: User preference calculation from quiz"""
        try:
            # First get some quiz songs
            songs_response = await self.client.get(f"{self.base_url}/quiz/songs?limit=5")
            if songs_response.status_code != 200:
                log_test("Preferences Calculation", "FAIL", "Could not get quiz songs")
                return False
            
            songs = songs_response.json()["quiz_songs"]
            
            # Create mock user ratings (like/dislike for each song)
            song_ratings = []
            for i, song in enumerate(songs):
                rating = "like" if i % 2 == 0 else "dislike"  # Alternate likes/dislikes
                song_ratings.append({
                    "song_id": song["id"],
                    "rating": rating
                })
            
            # Calculate preferences
            payload = {
                "user_id": self.user_id,
                "song_ratings": song_ratings
            }
            
            response = await self.client.post(
                f"{self.base_url}/quiz/calculate-preferences",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                user_profile = data.get("user_profile")
                
                if user_profile and "genre_preferences" in user_profile:
                    self.user_profile = user_profile  # Store for later tests
                    log_test("Preferences Calculation", "PASS", 
                           f"Generated profile with {len(user_profile['genre_preferences'])} genre preferences")
                    return True
                else:
                    log_test("Preferences Calculation", "FAIL", "Invalid user profile structure")
                    return False
            else:
                log_test("Preferences Calculation", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            log_test("Preferences Calculation", "ERROR", str(e))
            return False
    
    async def test_image_analysis(self):
        """Test 4: Image analysis (simple endpoint)"""
        try:
            # Create a test image
            test_image_bytes = create_test_image(color="blue")
            
            # Prepare multipart form data
            files = {
                "file": ("test_image.jpg", test_image_bytes, "image/jpeg")
            }
            
            response = await self.client.post(
                f"{self.base_url}/analyze-image",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["caption", "mood", "confidence"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    log_test("Image Analysis", "PASS", 
                           f"Analyzed image: mood='{data['mood']}', confidence={data['confidence']}")
                    return data
                else:
                    log_test("Image Analysis", "FAIL", f"Missing fields: {missing_fields}")
                    return {}
            else:
                log_test("Image Analysis", "FAIL", f"Status code: {response.status_code}")
                return {}
                
        except Exception as e:
            log_test("Image Analysis", "ERROR", str(e))
            return {}
    
    async def test_enhanced_analysis_and_recommendations(self) -> bool:
        """Test 5: Enhanced analysis with recommendations"""
        try:
            # Create a test image with a specific color to test mood detection
            test_image_bytes = create_test_image(color="green")  # Should trigger "nature" mood
            
            files = {
                "file": ("nature_test.jpg", test_image_bytes, "image/jpeg")
            }
            
            response = await self.client.post(
                f"{self.base_url}/analyze-and-recommend",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate structure
                required_fields = ["image_analysis", "recommendations"]
                optional_fields = ["music_profile", "search_queries"]
                
                missing_required = [field for field in required_fields if field not in data]
                
                if not missing_required:
                    recommendations = data.get("recommendations", [])
                    analysis = data.get("image_analysis", {})
                    
                    log_test("Enhanced Analysis & Recommendations", "PASS", 
                           f"Got {len(recommendations)} recommendations for mood: {analysis.get('mood', 'unknown')}")
                    
                    # Additional validation
                    if len(recommendations) > 0:
                        first_rec = recommendations[0]
                        rec_fields = ["name", "artist", "spotify_url"]
                        if all(field in first_rec for field in rec_fields):
                            print(f"   🎵 Sample recommendation: {first_rec['name']} by {first_rec['artist']}")
                        
                    return True
                else:
                    log_test("Enhanced Analysis & Recommendations", "FAIL", f"Missing fields: {missing_required}")
                    return False
            else:
                log_test("Enhanced Analysis & Recommendations", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            log_test("Enhanced Analysis & Recommendations", "ERROR", str(e))
            return False
    
    async def test_recommendations_with_profile(self) -> bool:
        """Test 6: Recommendations using user profile"""
        try:
            if not self.user_profile:
                log_test("Recommendations with Profile", "SKIP", "No user profile from previous test")
                return False
            
            payload = {
                "mood": "happy",
                "caption": "beautiful sunny day at the beach",
                "user_profile": self.user_profile
            }
            
            response = await self.client.post(
                f"{self.base_url}/recommendations",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", [])
                
                if len(recommendations) > 0:
                    log_test("Recommendations with Profile", "PASS", 
                           f"Got {len(recommendations)} personalized recommendations")
                    return True
                else:
                    log_test("Recommendations with Profile", "FAIL", "No recommendations returned")
                    return False
            else:
                log_test("Recommendations with Profile", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            log_test("Recommendations with Profile", "ERROR", str(e))
            return False
    
    async def test_song_search(self) -> bool:
        """Test 7: Song search functionality"""
        try:
            test_queries = ["happy music", "acoustic guitar", "electronic dance"]
            
            for query in test_queries:
                response = await self.client.get(
                    f"{self.base_url}/search/songs",
                    params={"query": query, "limit": 5}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if len(results) > 0:
                        log_test(f"Song Search ('{query}')", "PASS", f"Found {len(results)} songs")
                    else:
                        log_test(f"Song Search ('{query}')", "FAIL", "No search results")
                        return False
                else:
                    log_test(f"Song Search ('{query}')", "FAIL", f"Status code: {response.status_code}")
                    return False
            
            return True
                
        except Exception as e:
            log_test("Song Search", "ERROR", str(e))
            return False
    
    async def test_complete_user_journey(self) -> bool:
        """Test 8: Complete user journey simulation"""
        try:
            print("\n🚀 Testing Complete User Journey...")
            
            # Step 1: New user gets quiz songs
            print("   1. Getting quiz songs...")
            songs_response = await self.client.get(f"{self.base_url}/quiz/songs?limit=10")
            if songs_response.status_code != 200:
                log_test("Complete Journey - Quiz Songs", "FAIL", "Could not get quiz songs")
                return False
            
            songs = songs_response.json()["quiz_songs"]
            print(f"   ✓ Got {len(songs)} quiz songs")
            
            # Step 2: User completes quiz (simulate ratings)
            print("   2. Simulating quiz completion...")
            song_ratings = []
            for i, song in enumerate(songs[:8]):  # Rate 8 songs
                rating = "like" if (i + song['id'].__hash__()) % 3 != 0 else "dislike"
                song_ratings.append({"song_id": song["id"], "rating": rating})
            
            # Step 3: Calculate preferences
            print("   3. Calculating user preferences...")
            prefs_response = await self.client.post(
                f"{self.base_url}/quiz/calculate-preferences",
                json={"user_id": "journey_test_user", "song_ratings": song_ratings}
            )
            
            if prefs_response.status_code != 200:
                log_test("Complete Journey - Preferences", "FAIL", "Could not calculate preferences")
                return False
            
            user_profile = prefs_response.json()["user_profile"]
            print(f"   ✓ Generated user profile with {len(user_profile['genre_preferences'])} genre preferences")
            
            # Step 4: User uploads an image
            print("   4. Analyzing uploaded image...")
            test_image = create_test_image(color="orange")  # Should create energetic mood
            
            files = {"file": ("user_photo.jpg", test_image, "image/jpeg")}
            analysis_response = await self.client.post(
                f"{self.base_url}/analyze-and-recommend",
                files=files
            )
            
            if analysis_response.status_code != 200:
                log_test("Complete Journey - Image Analysis", "FAIL", "Could not analyze image")
                return False
            
            analysis_data = analysis_response.json()
            image_analysis = analysis_data["image_analysis"]
            recommendations = analysis_data["recommendations"]
            
            print(f"   ✓ Image analyzed: mood='{image_analysis['mood']}', got {len(recommendations)} recommendations")
            
            # Step 5: Get personalized recommendations using profile
            print("   5. Getting personalized recommendations...")
            personalized_response = await self.client.post(
                f"{self.base_url}/recommendations",
                json={
                    "mood": image_analysis["mood"],
                    "caption": image_analysis.get("caption", ""),
                    "user_profile": user_profile
                }
            )
            
            if personalized_response.status_code != 200:
                log_test("Complete Journey - Personalized Recs", "FAIL", "Could not get personalized recommendations")
                return False
            
            personalized_data = personalized_response.json()
            personalized_recs = personalized_data["recommendations"]
            
            print(f"   ✓ Got {len(personalized_recs)} personalized recommendations")
            
            # Success!
            log_test("Complete User Journey", "PASS", 
                   f"Successfully completed full journey: Quiz → Profile → Image → Recommendations")
            return True
            
        except Exception as e:
            log_test("Complete User Journey", "ERROR", str(e))
            return False

async def run_all_tests():
    """Run the complete test suite"""
    print("🧪 Starting End-to-End Test Suite for Image-to-Song App")
    print("="*60)
    
    start_time = time.time()
    
    async with EndToEndTester() as tester:
        # Core functionality tests
        await tester.test_health_check()
        await tester.test_quiz_songs_endpoint()
        await tester.test_preferences_calculation()
        
        # Image analysis tests
        image_analysis_result = await tester.test_image_analysis()
        await tester.test_enhanced_analysis_and_recommendations()
        
        # Recommendation tests
        await tester.test_recommendations_with_profile()
        await tester.test_song_search()
        
        # Integration test
        await tester.test_complete_user_journey()
    
    # Print summary
    duration = time.time() - start_time
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⏱️  Duration: {duration:.2f} seconds")
    
    if test_results['failed'] > 0:
        print("\n❌ FAILED TESTS:")
        for error in test_results['errors']:
            print(f"   - {error}")
    
    success_rate = (test_results['passed'] / test_results['total_tests']) * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🎉 EXCELLENT! Your app is working great!")
    elif success_rate >= 75:
        print("\n👍 GOOD! Most features are working, minor issues to fix.")
    else:
        print("\n⚠️  NEEDS ATTENTION! Several critical issues found.")
    
    return success_rate >= 75

if __name__ == "__main__":
    # Check if we should use a different URL
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
        print(f"Using custom base URL: {BASE_URL}")
    
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)
