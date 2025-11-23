"""
Simple image analyzer for mood detection when AI models are not available.
Provides fallback image analysis using color analysis and basic scene detection.
"""
import io
import random
from typing import Dict, Any, Tuple
from PIL import Image
import numpy as np

try:
    from ..utils.image_utils import ImageProcessor
    HAS_IMAGE_PROCESSOR = True
except ImportError:
    ImageProcessor = None
    HAS_IMAGE_PROCESSOR = False


class SimpleImageAnalyzer:
    """Simple image analyzer for mood detection"""
    
    def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """Enhanced image analyzer with better scene understanding"""
        try:
            print(f"SimpleImageAnalyzer: Starting analysis of {len(image_data)} bytes")
            
            # Open and analyze image
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            print(f"Image size: {width}x{height}")
            
            # Get dominant colors with enhanced analysis if available
            if HAS_IMAGE_PROCESSOR and ImageProcessor:
                try:
                    # Use advanced color extraction
                    enhanced_colors = ImageProcessor.extract_dominant_colors(image_data, num_colors=3)
                    if enhanced_colors:
                        # Use most dominant color
                        dominant_rgb = enhanced_colors[0]["rgb"]
                        r, g, b = dominant_rgb
                        print(f"Enhanced color analysis: {len(enhanced_colors)} colors, dominant: rgb({r},{g},{b})")
                    else:
                        r, g, b = 128, 128, 128
                except Exception as e:
                    print(f"Enhanced color analysis failed, using fallback: {e}")
                    r, g, b = self._fallback_color_analysis(image_data)
            else:
                # Fallback to basic color analysis
                image_rgb = image.convert('RGB')
                colors = image_rgb.getcolors(maxcolors=256*256*256)
                
                if colors:
                    dominant_color = max(colors, key=lambda x: x[0])[1]
                    # Ensure we have a tuple of RGB values
                    if isinstance(dominant_color, (tuple, list)) and len(dominant_color) >= 3:
                        r, g, b = dominant_color[:3]
                    else:
                        # Fallback if color format is unexpected
                        r, g, b = 128, 128, 128
                else:
                    r, g, b = 128, 128, 128
            
            # Enhanced color and context analysis (works for both enhanced and fallback modes)
            image_rgb = image.convert('RGB')
            scene_context = self._analyze_scene_context(image_rgb, width, height)
            mood, caption = self._determine_mood_and_scene(r, g, b, (r + g + b) / 3, 
                                                           max(r, g, b) - min(r, g, b), 
                                                           scene_context)
            
            color_info = {"dominant": f"rgb({r},{g},{b})", "brightness": (r + g + b) / 3}
            
            result = {
                "caption": caption,
                "mood": mood,
                "confidence": 0.85,
                "colors": color_info,
                "size": f"{width}x{height}",
                "analysis_method": "enhanced_color_context"
            }
            
            print(f"Analysis complete: {result}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"SimpleImageAnalyzer error: {error_msg}")
            return {
                "caption": "a beautiful scene captured in an image",
                "mood": "neutral",
                "confidence": 0.5,
                "error": error_msg,
                "analysis_method": "fallback"
            }
    
    def _determine_mood_from_colors(self, r: int, g: int, b: int, brightness: float, saturation: float) -> str:
        """Determine mood based on color analysis"""
        if brightness > 200 and saturation > 100:
            return "energetic"
        elif brightness > 180:
            return "happy"
        elif brightness < 80:
            return "melancholic"
        elif g > r and g > b:  # Green dominant
            return "nature"
        elif b > 150:  # Blue dominant
            return "peaceful"
        elif r > 150 and brightness > 100:  # Red/warm
            return "romantic"
        else:
            return "neutral"
    
    def _generate_caption(self, width: int, height: int, mood: str) -> str:
        """Generate a realistic caption based on image properties"""
        captions = {
            "energetic": [
                "dynamic scene with vibrant colors and movement",
                "action-packed moment with bright lighting",
                "energetic composition with bold visual elements"
            ],
            "happy": [
                "bright and cheerful scene with warm lighting",
                "joyful moment captured with vivid colors",
                "uplifting image with positive atmosphere"
            ],
            "peaceful": [
                "serene landscape with calm atmosphere",
                "tranquil scene with soft lighting",
                "peaceful moment in natural setting"
            ],
            "melancholic": [
                "moody scene with atmospheric lighting",
                "contemplative moment with subtle tones",
                "reflective composition with muted colors"
            ],
            "nature": [
                "beautiful natural landscape with greenery",
                "outdoor scene with natural elements",
                "scenic view of nature with organic forms"
            ],
            "romantic": [
                "romantic scene with warm ambient lighting",
                "intimate moment with soft color palette",
                "beautiful composition with romantic atmosphere"
            ]
        }
        
        mood_captions = captions.get(mood, ["scenic image with artistic composition"])
        return random.choice(mood_captions)
    
    def _analyze_scene_context(self, image_rgb, width: int, height: int) -> Dict[str, Any]:
        """Analyze image for scene context clues using color distribution"""
        try:
            # Convert to numpy array for analysis
            img_array = np.array(image_rgb)
            
            # Analyze color distribution in different regions
            h, w = img_array.shape[:2]
            
            # Sky region (top 1/3)
            sky_region = img_array[:h//3, :]
            sky_blue = np.mean(sky_region[:, :, 2])  # Blue channel
            
            # Ground/water region (bottom 1/3) 
            ground_region = img_array[2*h//3:, :]
            ground_green = np.mean(ground_region[:, :, 1])  # Green channel
            ground_blue = np.mean(ground_region[:, :, 2])   # Blue channel
            
            # Overall brightness distribution
            brightness_std = np.std(np.mean(img_array, axis=2))
            
            return {
                "sky_blue_intensity": sky_blue,
                "ground_green_intensity": ground_green,
                "ground_blue_intensity": ground_blue,
                "brightness_variation": brightness_std,
                "aspect_ratio": width / height if height > 0 else 1.0
            }
        except Exception:
            return {
                "sky_blue_intensity": 128,
                "ground_green_intensity": 128, 
                "ground_blue_intensity": 128,
                "brightness_variation": 50,
                "aspect_ratio": 1.0
            }
    
    def _determine_mood_and_scene(self, r: int, g: int, b: int, brightness: float, 
                                saturation: float, scene_context: Dict[str, Any]) -> Tuple[str, str]:
        """Enhanced mood and scene determination using color + context"""
        
        # Extract context clues
        sky_blue = scene_context.get("sky_blue_intensity", 128)
        ground_green = scene_context.get("ground_green_intensity", 128)
        ground_blue = scene_context.get("ground_blue_intensity", 128)
        brightness_var = scene_context.get("brightness_variation", 50)
        aspect_ratio = scene_context.get("aspect_ratio", 1.0)
        
        # Nature scene detection
        if (sky_blue > 150 and ground_green > 130) or (ground_blue > 140 and ground_green > 120):
            # Likely nature scene (sky + vegetation or water + vegetation)
            if brightness > 160:
                mood = "peaceful"
                caption = "serene natural landscape with bright sky and greenery"
            else:
                mood = "peaceful" 
                caption = "tranquil nature scene with soft natural lighting"
        
        # Water/lake scene detection  
        elif ground_blue > 160 and sky_blue > 140:
            mood = "peaceful"
            caption = "calm water scene reflecting the sky above"
        
        # Forest/green scene detection
        elif ground_green > 150 and g > r and g > b:
            mood = "nature"
            caption = "lush forest scene with abundant greenery"
            
        # Sunset/warm scene detection
        elif r > 160 and brightness > 140 and saturation > 80:
            mood = "romantic"
            caption = "warm scenic view with golden lighting"
            
        # High contrast/dramatic scene
        elif brightness_var > 80:
            if brightness > 150:
                mood = "energetic"
                caption = "dynamic scene with dramatic lighting contrasts"
            else:
                mood = "melancholic"
                caption = "moody scene with atmospheric shadows and highlights"
        
        # Fallback to basic color analysis
        else:
            if brightness > 200 and saturation > 100:
                mood = "energetic"
                caption = "vibrant scene with bold colors and bright lighting"
            elif brightness > 180:
                mood = "happy"
                caption = "bright and cheerful scene with warm lighting"
            elif brightness < 80:
                mood = "melancholic"
                caption = "contemplative moment with subtle tones"
            elif b > 150:  # Blue dominant
                mood = "peaceful"
                caption = "serene composition with cool blue tones"
            else:
                mood = "neutral"
                caption = "balanced composition with natural lighting"
        
        return mood, caption
    
    def _fallback_color_analysis(self, image_data: bytes) -> Tuple[int, int, int]:
        """Fallback color analysis when enhanced analysis fails"""
        try:
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            colors = image.getcolors(maxcolors=256*256*256)
            
            if colors:
                dominant_color = max(colors, key=lambda x: x[0])[1]
                if isinstance(dominant_color, (tuple, list)) and len(dominant_color) >= 3:
                    return dominant_color[:3]
            
            return (128, 128, 128)  # Default gray
        except Exception:
            return (128, 128, 128)  # Default gray


# Create global instance
simple_image_analyzer = SimpleImageAnalyzer()