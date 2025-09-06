"""
Enhanced Mood Analysis Service
Advanced image-to-music mood detection with multiple analysis layers.
"""

import re
import logging
from typing import Dict, List, Any, Tuple
import colorsys
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)

class EnhancedMoodAnalyzer:
    """
    Advanced mood analysis combining multiple factors:
    - Text sentiment from captions
    - Color psychology  
    - Object/scene recognition
    - Contextual understanding
    """
    
    def __init__(self):
        # Enhanced mood categories with sub-moods
        self.mood_categories = {
            "happy": {
                "keywords": ["happy", "joy", "smile", "celebration", "party", "fun", "bright", "cheerful", "excited", "laughter"],
                "colors": ["yellow", "orange", "bright", "warm"],
                "objects": ["party", "birthday", "wedding", "celebration", "friends"],
                "base_features": {
                    "valence": 0.8, "energy": 0.7, "danceability": 0.7, 
                    "acousticness": 0.3, "instrumentalness": 0.3, 
                    "speechiness": 0.1, "tempo": 130
                }
            },
            "peaceful": {
                "keywords": ["calm", "peaceful", "quiet", "serene", "relaxing", "tranquil", "meditation", "zen"],
                "colors": ["blue", "green", "soft", "pastel"],
                "objects": ["nature", "water", "forest", "garden", "spa"],
                "base_features": {
                    "valence": 0.6, "energy": 0.3, "danceability": 0.3, 
                    "acousticness": 0.8, "instrumentalness": 0.6, 
                    "speechiness": 0.1, "tempo": 80
                }
            },
            "melancholic": {
                "keywords": ["sad", "dark", "lonely", "rain", "gray", "melancholy", "depressed", "gloomy"],
                "colors": ["gray", "dark", "blue", "black"],
                "objects": ["rain", "storm", "winter", "empty"],
                "base_features": {
                    "valence": 0.2, "energy": 0.4, "danceability": 0.3, 
                    "acousticness": 0.6, "instrumentalness": 0.4, 
                    "speechiness": 0.1, "tempo": 70
                }
            },
            "energetic": {
                "keywords": ["energy", "action", "sports", "running", "dancing", "workout", "active", "dynamic"],
                "colors": ["red", "bright", "neon", "vibrant"],
                "objects": ["sports", "gym", "dance", "racing", "festival"],
                "base_features": {
                    "valence": 0.7, "energy": 0.9, "danceability": 0.8, 
                    "acousticness": 0.2, "instrumentalness": 0.2, 
                    "speechiness": 0.1, "tempo": 140
                }
            },
            "romantic": {
                "keywords": ["love", "romantic", "couple", "kiss", "romantic", "intimate", "tender"],
                "colors": ["pink", "red", "warm", "soft"],
                "objects": ["couple", "wedding", "flowers", "sunset", "candle"],
                "base_features": {
                    "valence": 0.7, "energy": 0.4, "danceability": 0.4, 
                    "acousticness": 0.5, "instrumentalness": 0.3, 
                    "speechiness": 0.1, "tempo": 90
                }
            },
            "nature": {
                "keywords": ["nature", "outdoor", "forest", "mountain", "beach", "ocean", "trees", "landscape"],
                "colors": ["green", "blue", "brown", "natural"],
                "objects": ["tree", "mountain", "ocean", "forest", "sky", "landscape"],
                "base_features": {
                    "valence": 0.6, "energy": 0.5, "danceability": 0.4, 
                    "acousticness": 0.7, "instrumentalness": 0.5, 
                    "speechiness": 0.1, "tempo": 100
                }
            },
            "mysterious": {
                "keywords": ["dark", "shadow", "mystery", "night", "mysterious", "unknown", "gothic"],
                "colors": ["black", "dark", "purple", "deep"],
                "objects": ["night", "shadow", "moon", "alley"],
                "base_features": {
                    "valence": 0.3, "energy": 0.6, "danceability": 0.5, 
                    "acousticness": 0.4, "instrumentalness": 0.6, 
                    "speechiness": 0.1, "tempo": 110
                }
            }
        }
        
        # Color psychology mapping (RGB to mood influence)
        self.color_psychology = {
            "red": {"energy": +0.3, "valence": +0.2, "arousal": +0.4},
            "blue": {"energy": -0.2, "valence": -0.1, "calmness": +0.4},
            "yellow": {"valence": +0.4, "energy": +0.2, "happiness": +0.5},
            "green": {"valence": +0.1, "energy": 0.0, "nature": +0.4},
            "purple": {"energy": +0.1, "mystery": +0.3, "sophistication": +0.2},
            "orange": {"energy": +0.3, "valence": +0.3, "warmth": +0.4},
            "pink": {"valence": +0.2, "romance": +0.4, "softness": +0.3},
            "black": {"energy": -0.3, "valence": -0.2, "sophistication": +0.2},
            "white": {"energy": +0.1, "purity": +0.4, "minimalism": +0.3},
            "gray": {"energy": -0.1, "valence": -0.1, "neutrality": +0.2}
        }

    def analyze_comprehensive_mood(self, mood_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive mood analysis combining multiple factors.
        
        Args:
            mood_analysis: Contains caption, dominant_colors, image_info
            
        Returns:
            Enhanced mood analysis with detailed breakdown
        """
        caption = mood_analysis.get("caption", "").lower()
        colors = mood_analysis.get("dominant_colors", [])
        
        # 1. Text-based mood analysis
        text_mood = self._analyze_text_mood(caption)
        
        # 2. Color-based mood analysis  
        color_mood = self._analyze_color_mood(colors)
        
        # 3. Scene/object analysis
        scene_mood = self._analyze_scene_context(caption)
        
        # 4. Combine all analyses
        combined_mood = self._combine_mood_analyses(text_mood, color_mood, scene_mood)
        
        # 5. Generate final audio features
        audio_features = self._mood_to_spotify_features(combined_mood)
        
        return {
            "primary_mood": combined_mood["primary_mood"],
            "mood_confidence": combined_mood["confidence"],
            "mood_breakdown": {
                "text_analysis": text_mood,
                "color_analysis": color_mood, 
                "scene_analysis": scene_mood
            },
            "audio_features": audio_features,
            "mood_explanation": self._generate_mood_explanation(combined_mood, caption),
            "recommended_genres": self._suggest_music_genres(combined_mood)
        }

    def _analyze_text_mood(self, caption: str) -> Dict[str, Any]:
        """Analyze mood from caption text."""
        mood_scores = {}
        
        for mood, config in self.mood_categories.items():
            score = 0
            matched_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in caption:
                    score += 1
                    matched_keywords.append(keyword)
            
            mood_scores[mood] = {
                "score": score,
                "matched_keywords": matched_keywords,
                "confidence": min(score / len(config["keywords"]), 1.0)
            }
        
        # Find primary mood
        primary_mood = max(mood_scores.items(), key=lambda x: x[1]["score"])
        
        return {
            "primary_mood": primary_mood[0] if primary_mood[1]["score"] > 0 else "neutral",
            "all_scores": mood_scores,
            "confidence": primary_mood[1]["confidence"] if primary_mood[1]["score"] > 0 else 0.1
        }

    def _analyze_color_mood(self, colors: List[Dict]) -> Dict[str, Any]:
        """Analyze mood from dominant colors."""
        if not colors:
            return {"primary_mood": "neutral", "confidence": 0.1, "color_influences": {}}
        
        color_influences = {}
        total_mood_impact = {}
        
        for color_data in colors[:3]:  # Top 3 colors
            rgb = color_data.get("rgb", (128, 128, 128))
            percentage = color_data.get("percentage", 0)
            
            # Convert RGB to color name
            color_name = self._rgb_to_color_name(rgb)
            
            # Get psychological impact
            if color_name in self.color_psychology:
                impact = self.color_psychology[color_name]
                weight = percentage / 100.0
                
                color_influences[color_name] = {
                    "percentage": percentage,
                    "psychological_impact": impact,
                    "weight": weight
                }
                
                # Accumulate weighted impact
                for attribute, value in impact.items():
                    if attribute not in total_mood_impact:
                        total_mood_impact[attribute] = 0
                    total_mood_impact[attribute] += value * weight
        
        # Determine primary color mood
        primary_color_mood = self._color_impact_to_mood(total_mood_impact)
        
        return {
            "primary_mood": primary_color_mood,
            "color_influences": color_influences,
            "total_impact": total_mood_impact,
            "confidence": min(len(color_influences) * 0.3, 0.8)
        }

    def _analyze_scene_context(self, caption: str) -> Dict[str, Any]:
        """Analyze scene context for mood."""
        scene_indicators = {
            "indoor": ["room", "kitchen", "bedroom", "office", "house", "building"],
            "outdoor": ["outside", "park", "street", "garden", "yard", "field"],
            "nature": ["tree", "forest", "mountain", "ocean", "lake", "sky", "beach"],
            "urban": ["city", "building", "street", "car", "traffic", "downtown"],
            "social": ["people", "group", "crowd", "family", "friends", "couple"],
            "solitary": ["alone", "single", "one person", "individual"],
            "time_day": ["morning", "day", "noon", "bright", "sunny"],
            "time_night": ["night", "dark", "evening", "sunset", "dusk"]
        }
        
        detected_scenes = {}
        for scene_type, keywords in scene_indicators.items():
            matches = [kw for kw in keywords if kw in caption]
            if matches:
                detected_scenes[scene_type] = matches
        
        # Context-based mood inference
        context_mood = "neutral"
        confidence = 0.1
        
        if "nature" in detected_scenes:
            context_mood = "peaceful"
            confidence = 0.6
        elif "social" in detected_scenes and "time_day" in detected_scenes:
            context_mood = "happy"
            confidence = 0.5
        elif "time_night" in detected_scenes:
            context_mood = "mysterious"
            confidence = 0.4
        elif "urban" in detected_scenes:
            context_mood = "energetic"
            confidence = 0.3
        
        return {
            "primary_mood": context_mood,
            "detected_scenes": detected_scenes,
            "confidence": confidence
        }

    def _combine_mood_analyses(self, text_mood: Dict, color_mood: Dict, scene_mood: Dict) -> Dict[str, Any]:
        """Combine all mood analyses into final result."""
        # Weight the different analyses
        weights = {
            "text": 0.5,    # Text is most reliable
            "color": 0.3,   # Colors provide good context
            "scene": 0.2    # Scene context is supportive
        }
        
        # Collect all mood suggestions with weighted confidence
        mood_candidates = {}
        
        # Add text mood
        text_primary = text_mood["primary_mood"]
        if text_primary != "neutral":
            mood_candidates[text_primary] = text_mood["confidence"] * weights["text"]
        
        # Add color mood
        color_primary = color_mood["primary_mood"]  
        if color_primary != "neutral":
            if color_primary in mood_candidates:
                mood_candidates[color_primary] += color_mood["confidence"] * weights["color"]
            else:
                mood_candidates[color_primary] = color_mood["confidence"] * weights["color"]
        
        # Add scene mood
        scene_primary = scene_mood["primary_mood"]
        if scene_primary != "neutral":
            if scene_primary in mood_candidates:
                mood_candidates[scene_primary] += scene_mood["confidence"] * weights["scene"]
            else:
                mood_candidates[scene_primary] = scene_mood["confidence"] * weights["scene"]
        
        # Determine final mood
        if mood_candidates:
            primary_mood = max(mood_candidates.items(), key=lambda x: x[1])
            final_mood = primary_mood[0]
            final_confidence = min(primary_mood[1], 1.0)
        else:
            final_mood = "peaceful"  # Default neutral-positive mood
            final_confidence = 0.2
        
        return {
            "primary_mood": final_mood,
            "confidence": final_confidence,
            "all_candidates": mood_candidates,
            "analysis_sources": {
                "text": text_mood,
                "color": color_mood,
                "scene": scene_mood
            }
        }

    def _mood_to_spotify_features(self, combined_mood: Dict[str, Any]) -> Dict[str, float]:
        """Convert combined mood analysis to Spotify audio features."""
        primary_mood = combined_mood["primary_mood"]
        confidence = combined_mood["confidence"]
        
        # Get base features for the mood
        if primary_mood in self.mood_categories:
            base_features = self.mood_categories[primary_mood]["base_features"].copy()
        else:
            # Default neutral features
            base_features = {
                "valence": 0.5, "energy": 0.5, "danceability": 0.5,
                "acousticness": 0.5, "instrumentalness": 0.3, 
                "speechiness": 0.1, "tempo": 120
            }
        
        # Apply confidence scaling (low confidence = move toward neutral)
        neutral_features = {
            "valence": 0.5, "energy": 0.5, "danceability": 0.5,
            "acousticness": 0.5, "instrumentalness": 0.3, 
            "speechiness": 0.1, "tempo": 120
        }
        
        final_features = {}
        for feature, value in base_features.items():
            neutral_value = neutral_features.get(feature, 0.5)
            # Blend based on confidence: high confidence = use mood value, low confidence = blend with neutral
            final_features[feature] = value * confidence + neutral_value * (1 - confidence)
        
        # Add some randomness for variety (±10%)
        import random
        for feature in ["valence", "energy", "danceability", "acousticness", "instrumentalness"]:
            if feature in final_features:
                variation = random.uniform(-0.1, 0.1)
                final_features[feature] = max(0.0, min(1.0, final_features[feature] + variation))
        
        # Ensure tempo is reasonable
        if "tempo" in final_features:
            final_features["tempo"] = max(60, min(200, final_features["tempo"] + random.uniform(-10, 10)))
        
        return final_features

    def _rgb_to_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB values to nearest color name."""
        r, g, b = rgb
        
        # Simple color classification
        if r > 200 and g < 100 and b < 100:
            return "red"
        elif r > 200 and g > 200 and b < 100:
            return "yellow"
        elif r < 100 and g > 200 and b < 100:
            return "green"
        elif r < 100 and g < 100 and b > 200:
            return "blue"
        elif r > 150 and g < 150 and b > 150:
            return "purple"
        elif r > 200 and g > 150 and b < 100:
            return "orange"
        elif r > 200 and g > 150 and b > 150:
            return "pink"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        elif r > 200 and g > 200 and b > 200:
            return "white"
        else:
            return "gray"

    def _color_impact_to_mood(self, impact: Dict[str, float]) -> str:
        """Convert color psychological impact to mood category."""
        if "happiness" in impact and impact["happiness"] > 0.3:
            return "happy"
        elif "calmness" in impact and impact["calmness"] > 0.3:
            return "peaceful"
        elif "energy" in impact and impact["energy"] > 0.3:
            return "energetic"
        elif "romance" in impact and impact["romance"] > 0.3:
            return "romantic"
        elif "nature" in impact and impact["nature"] > 0.3:
            return "nature"
        elif "mystery" in impact and impact["mystery"] > 0.2:
            return "mysterious"
        else:
            return "neutral"

    def _generate_mood_explanation(self, combined_mood: Dict, caption: str) -> str:
        """Generate human-readable explanation of mood analysis."""
        primary_mood = combined_mood["primary_mood"]
        confidence = combined_mood["confidence"]
        
        explanations = {
            "happy": "The image suggests a joyful, upbeat mood with bright and positive elements.",
            "peaceful": "The image conveys a calm, serene atmosphere perfect for relaxation.",
            "melancholic": "The image has a more somber, reflective tone with darker elements.",
            "energetic": "The image shows dynamic, high-energy content that's exciting and active.",
            "romantic": "The image has romantic, intimate qualities that suggest love and tenderness.",
            "nature": "The image features natural elements that evoke outdoor, earthy feelings.",
            "mysterious": "The image has mysterious, intriguing qualities with darker undertones."
        }
        
        base_explanation = explanations.get(primary_mood, "The image has a neutral, balanced mood.")
        
        if confidence > 0.7:
            confidence_text = "I'm quite confident in this assessment."
        elif confidence > 0.4:
            confidence_text = "This assessment is moderately confident."
        else:
            confidence_text = "This is a tentative assessment with some uncertainty."
        
        return f"{base_explanation} {confidence_text}"

    def _suggest_music_genres(self, combined_mood: Dict) -> List[str]:
        """Suggest music genres based on mood analysis."""
        mood_to_genres = {
            "happy": ["Pop", "Funk", "Dance", "Reggae", "Gospel"],
            "peaceful": ["Ambient", "Classical", "New Age", "Folk", "Acoustic"],
            "melancholic": ["Blues", "Indie", "Alternative", "Sad Songs", "Ballads"],
            "energetic": ["Electronic", "Rock", "Hip-Hop", "Fitness", "Punk"],
            "romantic": ["R&B", "Soul", "Love Songs", "Smooth Jazz", "Romantic"],
            "nature": ["World Music", "Instrumental", "Celtic", "Environmental"],
            "mysterious": ["Dark Ambient", "Gothic", "Trip-Hop", "Experimental"]
        }
        
        primary_mood = combined_mood["primary_mood"]
        return mood_to_genres.get(primary_mood, ["Pop", "Alternative"])

# Global service instance
enhanced_mood_analyzer = EnhancedMoodAnalyzer()
