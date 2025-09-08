"""
Enhanced Image-to-Music Mapping System
Combines BLIP scene detection with color mood analysis for intelligent music recommendations.
"""
from typing import Dict, List, Any
import re

class ImageMusicMapper:
    """
    Maps image analysis results (scene + mood) to music characteristics and genres.
    """
    
    def __init__(self):
        # Scene-based music mappings
        self.scene_mappings = {
            # Natural scenes
            "beach": {"genres": ["reggae", "tropical", "chill"], "energy": 0.6, "valence": 0.8},
            "ocean": {"genres": ["ambient", "chill", "new age"], "energy": 0.4, "valence": 0.7},
            "mountain": {"genres": ["folk", "country", "ambient"], "energy": 0.5, "valence": 0.6},
            "forest": {"genres": ["folk", "ambient", "nature sounds"], "energy": 0.4, "valence": 0.6},
            "sunset": {"genres": ["jazz", "chill", "romantic"], "energy": 0.3, "valence": 0.7},
            "sunrise": {"genres": ["upbeat", "pop", "electronic"], "energy": 0.7, "valence": 0.8},
            "lake": {"genres": ["ambient", "classical", "chill"], "energy": 0.3, "valence": 0.6},
            "park": {"genres": ["pop", "indie", "acoustic"], "energy": 0.6, "valence": 0.7},
            "garden": {"genres": ["classical", "acoustic", "folk"], "energy": 0.4, "valence": 0.7},
            "field": {"genres": ["country", "folk", "acoustic"], "energy": 0.5, "valence": 0.6},
            
            # Urban scenes
            "city": {"genres": ["hip-hop", "electronic", "pop"], "energy": 0.8, "valence": 0.6},
            "street": {"genres": ["hip-hop", "rock", "urban"], "energy": 0.7, "valence": 0.5},
            "building": {"genres": ["electronic", "ambient", "modern"], "energy": 0.6, "valence": 0.5},
            "skyline": {"genres": ["electronic", "pop", "ambient"], "energy": 0.7, "valence": 0.6},
            "traffic": {"genres": ["electronic", "techno", "urban"], "energy": 0.8, "valence": 0.4},
            "cafe": {"genres": ["jazz", "acoustic", "indie"], "energy": 0.4, "valence": 0.7},
            "restaurant": {"genres": ["jazz", "classical", "ambient"], "energy": 0.4, "valence": 0.7},
            
            # Indoor scenes
            "room": {"genres": ["acoustic", "indie", "chill"], "energy": 0.5, "valence": 0.6},
            "bedroom": {"genres": ["chill", "r&b", "acoustic"], "energy": 0.3, "valence": 0.6},
            "kitchen": {"genres": ["pop", "indie", "acoustic"], "energy": 0.6, "valence": 0.7},
            "living room": {"genres": ["acoustic", "jazz", "chill"], "energy": 0.4, "valence": 0.7},
            "office": {"genres": ["ambient", "electronic", "classical"], "energy": 0.5, "valence": 0.5},
            
            # Activity scenes
            "concert": {"genres": ["rock", "pop", "electronic"], "energy": 0.9, "valence": 0.8},
            "party": {"genres": ["pop", "dance", "hip-hop"], "energy": 0.9, "valence": 0.8},
            "dance": {"genres": ["dance", "electronic", "pop"], "energy": 0.9, "valence": 0.8},
            "gym": {"genres": ["electronic", "hip-hop", "rock"], "energy": 0.9, "valence": 0.7},
            "workout": {"genres": ["electronic", "hip-hop", "rock"], "energy": 0.9, "valence": 0.7},
            "yoga": {"genres": ["ambient", "new age", "classical"], "energy": 0.2, "valence": 0.7},
            "meditation": {"genres": ["ambient", "new age", "nature sounds"], "energy": 0.1, "valence": 0.6},
            
            # Weather/time
            "rain": {"genres": ["jazz", "blues", "ambient"], "energy": 0.3, "valence": 0.4},
            "snow": {"genres": ["classical", "ambient", "folk"], "energy": 0.3, "valence": 0.6},
            "sunny": {"genres": ["pop", "reggae", "upbeat"], "energy": 0.8, "valence": 0.9},
            "cloudy": {"genres": ["indie", "alternative", "ambient"], "energy": 0.4, "valence": 0.5},
            "night": {"genres": ["jazz", "r&b", "electronic"], "energy": 0.4, "valence": 0.5},
            
            # People/social
            "group": {"genres": ["pop", "dance", "party"], "energy": 0.7, "valence": 0.8},
            "crowd": {"genres": ["pop", "rock", "electronic"], "energy": 0.8, "valence": 0.7},
            "family": {"genres": ["acoustic", "folk", "pop"], "energy": 0.6, "valence": 0.8},
            "children": {"genres": ["pop", "children's music", "upbeat"], "energy": 0.7, "valence": 0.9},
            "wedding": {"genres": ["romantic", "classical", "pop"], "energy": 0.6, "valence": 0.9},
            
            # Animals
            "dog": {"genres": ["upbeat", "pop", "acoustic"], "energy": 0.7, "valence": 0.8},
            "cat": {"genres": ["chill", "jazz", "acoustic"], "energy": 0.4, "valence": 0.7},
            "bird": {"genres": ["folk", "acoustic", "nature sounds"], "energy": 0.5, "valence": 0.7},
            
            # Food
            "food": {"genres": ["jazz", "acoustic", "world music"], "energy": 0.5, "valence": 0.7},
            "cooking": {"genres": ["jazz", "world music", "acoustic"], "energy": 0.6, "valence": 0.7},
            "dinner": {"genres": ["jazz", "classical", "romantic"], "energy": 0.4, "valence": 0.7},
        }
        
        # Mood-based adjustments
        self.mood_adjustments = {
            "energetic": {"energy_boost": 0.3, "valence_boost": 0.2, "genres": ["electronic", "dance", "pop"]},
            "happy": {"energy_boost": 0.2, "valence_boost": 0.3, "genres": ["pop", "upbeat", "reggae"]},
            "peaceful": {"energy_boost": -0.2, "valence_boost": 0.1, "genres": ["ambient", "classical", "new age"]},
            "melancholic": {"energy_boost": -0.3, "valence_boost": -0.3, "genres": ["blues", "alternative", "indie"]},
            "nature": {"energy_boost": -0.1, "valence_boost": 0.1, "genres": ["folk", "ambient", "nature sounds"]},
            "romantic": {"energy_boost": -0.1, "valence_boost": 0.2, "genres": ["r&b", "jazz", "romantic"]},
            "calm": {"energy_boost": -0.2, "valence_boost": 0.1, "genres": ["ambient", "classical", "chill"]},
            "neutral": {"energy_boost": 0, "valence_boost": 0, "genres": ["pop", "indie", "acoustic"]}
        }
    
    def analyze_scene_content(self, scene_description: str) -> Dict[str, Any]:
        """
        Extract scene elements from BLIP caption
        """
        if not scene_description:
            return {"elements": [], "confidence": 0.0}
        
        scene_description = scene_description.lower()
        detected_elements = []
        confidence_scores = []
        
        # Check for scene mappings
        for scene_key, mapping in self.scene_mappings.items():
            if scene_key in scene_description:
                confidence = len(scene_key) / len(scene_description)  # Rough confidence based on match length
                detected_elements.append({
                    "element": scene_key,
                    "mapping": mapping,
                    "confidence": min(confidence * 2, 1.0)  # Cap at 1.0
                })
                confidence_scores.append(confidence)
        
        # If no direct matches, try partial matches
        if not detected_elements:
            # Common words that might indicate scene types
            word_mappings = {
                "water": "ocean",
                "tree": "forest",
                "road": "street", 
                "house": "building",
                "car": "traffic",
                "person": "group",
                "people": "crowd",
                "sky": "sunny",
                "cloud": "cloudy"
            }
            
            for word, scene in word_mappings.items():
                if word in scene_description and scene in self.scene_mappings:
                    detected_elements.append({
                        "element": scene,
                        "mapping": self.scene_mappings[scene],
                        "confidence": 0.6  # Lower confidence for partial matches
                    })
                    confidence_scores.append(0.6)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        return {
            "elements": detected_elements,
            "confidence": avg_confidence
        }
    
    def create_music_profile(self, scene_description: str, mood: str, colors: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive music profile from image analysis
        """
        # Analyze scene content
        scene_analysis = self.analyze_scene_content(scene_description)
        
        # Start with base values
        base_energy = 0.5
        base_valence = 0.5
        recommended_genres = set()
        
        # Apply scene-based adjustments
        scene_weight = 0.7  # How much scene influences the recommendation
        mood_weight = 0.3   # How much mood influences the recommendation
        
        if scene_analysis["elements"]:
            # Weight by confidence and combine multiple scene elements
            total_weight = 0
            weighted_energy = 0
            weighted_valence = 0
            
            for element_data in scene_analysis["elements"]:
                mapping = element_data["mapping"]
                confidence = element_data["confidence"]
                
                weighted_energy += mapping["energy"] * confidence
                weighted_valence += mapping["valence"] * confidence
                total_weight += confidence
                
                # Add genres with confidence weighting
                for genre in mapping["genres"]:
                    recommended_genres.add(genre)
            
            if total_weight > 0:
                base_energy = (weighted_energy / total_weight) * scene_weight + base_energy * (1 - scene_weight)
                base_valence = (weighted_valence / total_weight) * scene_weight + base_valence * (1 - scene_weight)
        
        # Apply mood adjustments
        if mood in self.mood_adjustments:
            mood_adj = self.mood_adjustments[mood]
            base_energy = max(0, min(1, base_energy + mood_adj["energy_boost"] * mood_weight))
            base_valence = max(0, min(1, base_valence + mood_adj["valence_boost"] * mood_weight))
            
            # Add mood-based genres
            for genre in mood_adj["genres"]:
                recommended_genres.add(genre)
        
        # Color-based fine-tuning
        brightness = colors.get("brightness", 128)
        saturation = colors.get("saturation", 0)
        
        # Brightness affects energy and valence
        if brightness > 180:
            base_energy += 0.1
            base_valence += 0.1
        elif brightness < 100:
            base_energy -= 0.1
            base_valence -= 0.1
        
        # High saturation adds energy
        if saturation > 100:
            base_energy += 0.1
        
        # Ensure values stay in bounds
        base_energy = max(0.1, min(0.9, base_energy))
        base_valence = max(0.1, min(0.9, base_valence))
        
        # Calculate other audio features based on energy and valence
        audio_features = {
            "energy": base_energy,
            "valence": base_valence,
            "danceability": min(0.9, base_energy + 0.1),
            "acousticness": max(0.1, 0.8 - base_energy),  # Lower energy = more acoustic
            "instrumentalness": 0.3 if mood in ["peaceful", "melancholic", "calm"] else 0.1
        }
        
        return {
            "recommended_genres": list(recommended_genres)[:5],  # Top 5 genres
            "audio_features": audio_features,
            "scene_analysis": scene_analysis,
            "mood": mood,
            "confidence": scene_analysis["confidence"],
            "analysis_method": "hybrid_scene_mood_mapping"
        }
    
    def get_search_queries(self, music_profile: Dict[str, Any], mood: str) -> List[str]:
        """
        Generate Spotify search queries based on music profile
        """
        queries = []
        genres = music_profile.get("recommended_genres", [])
        audio_features = music_profile.get("audio_features", {})
        
        # Genre-based queries
        for genre in genres[:3]:  # Top 3 genres
            queries.extend([
                f"{genre}",
                f"{mood} {genre}",
                f"top {genre} songs"
            ])
        
        # Mood-based queries
        mood_queries = {
            "energetic": ["workout music", "high energy songs", "pump up songs"],
            "happy": ["feel good music", "upbeat songs", "happy playlist"],
            "peaceful": ["calm music", "relaxing songs", "chill playlist"],
            "melancholic": ["sad songs", "emotional music", "melancholy playlist"],
            "romantic": ["love songs", "romantic music", "date night playlist"],
            "nature": ["nature sounds", "outdoor music", "acoustic songs"]
        }
        
        if mood in mood_queries:
            queries.extend(mood_queries[mood])
        
        # Remove duplicates while preserving order
        unique_queries = []
        seen = set()
        for query in queries:
            if query not in seen:
                unique_queries.append(query)
                seen.add(query)
        
        return unique_queries[:8]  # Return top 8 unique queries

# Global mapper instance
image_music_mapper = ImageMusicMapper()
