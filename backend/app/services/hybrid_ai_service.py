"""
Hybrid AI Service combining BLIP model for object/scene detection 
with SimpleImageAnalyzer for mood detection.
This gives us both semantic understanding and emotional context.
"""
import asyncio
import io
import time
import logging
import random
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

from ..core.config import settings

# Set up logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

class SimpleColorAnalyzer:
    """Extract mood and color information from images"""
    
    def analyze_colors_and_mood(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image colors and determine mood"""
        try:
            width, height = image.size
            
            # Get dominant colors
            image_rgb = image.convert('RGB')
            colors = image_rgb.getcolors(maxcolors=256*256*256)
            
            if colors:
                dominant_color = max(colors, key=lambda x: x[0])[1]
                # Ensure we have a tuple of RGB values
                if isinstance(dominant_color, (tuple, list)) and len(dominant_color) >= 3:
                    r, g, b = dominant_color[:3]
                else:
                    r, g, b = 128, 128, 128
                
                # Color-based mood detection
                brightness = (r + g + b) / 3
                saturation = max(r, g, b) - min(r, g, b)
                
                mood = self._determine_mood_from_colors(r, g, b, brightness, saturation)
                color_info = {
                    "dominant": f"rgb({r},{g},{b})", 
                    "brightness": brightness,
                    "saturation": saturation
                }
            else:
                mood = "neutral"
                r, g, b = 128, 128, 128
                brightness = 128
                color_info = {
                    "dominant": f"rgb({r},{g},{b})", 
                    "brightness": brightness,
                    "saturation": 0
                }
            
            return {
                "mood": mood,
                "colors": color_info,
                "size": f"{width}x{height}"
            }
            
        except Exception as e:
            logger.warning(f"Color analysis failed: {e}")
            return {
                "mood": "neutral",
                "colors": {"dominant": "rgb(128,128,128)", "brightness": 128, "saturation": 0},
                "size": "unknown"
            }
    
    def _determine_mood_from_colors(self, r: int, g: int, b: int, brightness: float, saturation: float) -> str:
        """Determine mood based on color analysis"""
        # High energy colors
        if brightness > 200 and saturation > 100:
            return "energetic"
        # Bright and happy
        elif brightness > 180:
            return "happy"
        # Dark and moody
        elif brightness < 80:
            return "melancholic"
        # Green dominant - nature
        elif g > r and g > b and g > 120:
            return "nature"
        # Blue dominant - peaceful
        elif b > 150 and b > r and b > g:
            return "peaceful"
        # Red/warm dominant - romantic
        elif r > 150 and brightness > 100 and (r > b + 30):
            return "romantic"
        # Muted colors - calm
        elif saturation < 50 and brightness > 100:
            return "calm"
        else:
            return "neutral"

class HybridImageService:
    """
    Hybrid service combining BLIP for scene understanding and color analysis for mood.
    Uses the smaller BLIP model (~1GB) for fast object/scene detection.
    """
    
    def __init__(self):
        self.model: Optional[BlipForConditionalGeneration] = None
        self.processor: Optional[BlipProcessor] = None
        self.device = torch.device("cpu")  # CPU optimized
        self.model_name = "Salesforce/blip-image-captioning-base"  # ~1GB vs 15GB
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.is_loaded = False
        self.color_analyzer = SimpleColorAnalyzer()
        
        logger.info(f"Initialized HybridImageService with model: {self.model_name}")

    async def load_model(self) -> None:
        """Load the BLIP model asynchronously"""
        if self.is_loaded:
            logger.info("Model already loaded")
            return
            
        logger.info("Loading BLIP model for scene detection...")
        start_time = time.time()
        
        try:
            # Load in thread to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._load_model_sync
            )
            
            load_time = time.time() - start_time
            logger.info(f"✅ BLIP model loaded successfully in {load_time:.2f}s")
            self.is_loaded = True
            
        except Exception as e:
            logger.error(f"❌ Failed to load BLIP model: {e}")
            self.is_loaded = False
            raise

    def _load_model_sync(self) -> None:
        """Synchronous model loading"""
        try:
            # Load processor
            self.processor = BlipProcessor.from_pretrained(self.model_name)
            
            # Load model with CPU optimizations
            self.model = BlipForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,  # CPU works better with float32
                low_cpu_mem_usage=True
            )
            
            # Set to evaluation mode
            self.model.eval()
            
        except Exception as e:
            logger.error(f"Synchronous model loading failed: {e}")
            raise

    async def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Hybrid analysis: BLIP for scene detection + color analysis for mood
        """
        try:
            logger.info(f"🔍 HybridImageService: Starting analysis of {len(image_data)} bytes")
            
            # Load image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            # Always do color analysis (fast and reliable)
            color_result = self.color_analyzer.analyze_colors_and_mood(image)
            
            # Try BLIP analysis if model is loaded
            if self.is_loaded and self.model and self.processor:
                try:
                    scene_result = await self._analyze_scene_with_blip(image)
                    
                    # Combine both analyses
                    combined_caption = self._create_enhanced_caption(
                        scene_result["caption"], 
                        color_result["mood"]
                    )
                    
                    result = {
                        "status": "success",
                        "caption": combined_caption,
                        "scene_description": scene_result["caption"],
                        "mood": color_result["mood"],
                        "confidence": 0.9,
                        "colors": color_result["colors"],
                        "size": color_result["size"],
                        "analysis_method": "hybrid_blip_color",
                        "scene_confidence": scene_result["confidence"]
                    }
                    
                except Exception as e:
                    logger.warning(f"BLIP analysis failed, using color-only: {e}")
                    result = self._fallback_to_color_only(color_result, image_data)
            else:
                logger.info("BLIP model not loaded, using color-only analysis")
                result = self._fallback_to_color_only(color_result, image_data)
            
            logger.info(f"✅ Hybrid analysis complete: {result['analysis_method']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Hybrid analysis failed: {e}")
            return {
                "status": "error",
                "caption": "a beautiful scene captured in an image",
                "mood": "neutral",
                "confidence": 0.5,
                "error": str(e),
                "analysis_method": "fallback"
            }

    async def _analyze_scene_with_blip(self, image: Image.Image) -> Dict[str, Any]:
        """Use BLIP to analyze scene content"""
        try:
            # Process in thread to avoid blocking
            caption = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._generate_caption_sync, image
            )
            
            return {
                "caption": caption,
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"BLIP caption generation failed: {e}")
            raise

    def _generate_caption_sync(self, image: Image.Image) -> str:
        """Synchronous caption generation with BLIP"""
        try:
            if not self.processor or not self.model:
                raise RuntimeError("Model or processor not available")
                
            # Process inputs
            inputs = self.processor(image, return_tensors="pt")  # type: ignore
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(  # type: ignore
                    **inputs,  # type: ignore
                    max_length=50,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode caption
            caption = self.processor.decode(generated_ids[0], skip_special_tokens=True)  # type: ignore
            return caption.strip()
            
        except Exception as e:
            logger.error(f"Caption generation error: {e}")
            raise

    def _create_enhanced_caption(self, scene_caption: str, mood: str) -> str:
        """Combine scene description with mood for enhanced caption"""
        mood_adjectives = {
            "energetic": ["vibrant", "dynamic", "lively"],
            "happy": ["cheerful", "bright", "joyful"],
            "peaceful": ["serene", "tranquil", "calm"],
            "melancholic": ["moody", "atmospheric", "contemplative"],
            "nature": ["natural", "organic", "scenic"],
            "romantic": ["romantic", "intimate", "warm"],
            "calm": ["peaceful", "gentle", "soothing"],
            "neutral": ["beautiful", "artistic", "captivating"]
        }
        
        adjective = random.choice(mood_adjectives.get(mood, ["beautiful"]))
        
        # Enhance the scene caption with mood
        if scene_caption and len(scene_caption) > 5:
            return f"{adjective} {scene_caption}"
        else:
            return f"{adjective} scene with {mood} atmosphere"

    def _fallback_to_color_only(self, color_result: Dict[str, Any], image_data: bytes) -> Dict[str, Any]:
        """Fallback to color-only analysis with template captions"""
        mood = color_result["mood"]
        
        # Template captions based on mood
        template_captions = {
            "energetic": [
                "dynamic scene with vibrant colors and movement",
                "action-packed moment with bright lighting"
            ],
            "happy": [
                "bright and cheerful scene with warm lighting",
                "joyful moment captured with vivid colors"
            ],
            "peaceful": [
                "serene landscape with calm atmosphere",
                "tranquil scene with soft lighting"
            ],
            "melancholic": [
                "moody scene with atmospheric lighting",
                "contemplative moment with subtle tones"
            ],
            "nature": [
                "beautiful natural landscape with greenery",
                "outdoor scene with natural elements"
            ],
            "romantic": [
                "romantic scene with warm ambient lighting",
                "intimate moment with soft color palette"
            ],
            "calm": [
                "peaceful composition with gentle tones",
                "serene moment with balanced lighting"
            ],
            "neutral": [
                "artistic composition with balanced elements",
                "captivating scene with interesting details"
            ]
        }
        
        caption = random.choice(template_captions.get(mood, ["beautiful artistic composition"]))
        
        return {
            "status": "success",
            "caption": caption,
            "scene_description": None,
            "mood": color_result["mood"],
            "confidence": 0.75,
            "colors": color_result["colors"],
            "size": color_result["size"],
            "analysis_method": "color_only_templates"
        }

    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information and status"""
        return {
            "service": "HybridImageService",
            "model_name": self.model_name,
            "status": "loaded" if self.is_loaded else "not_loaded",
            "device": str(self.device),
            "features": ["scene_detection", "mood_analysis", "color_analysis"],
            "fallback_available": True
        }

    async def cleanup(self) -> None:
        """Cleanup resources"""
        logger.info("Cleaning up HybridImageService...")
        
        if self.model:
            del self.model
            self.model = None
            
        if self.processor:
            del self.processor
            self.processor = None
            
        if hasattr(torch.cuda, 'empty_cache'):
            torch.cuda.empty_cache()
            
        self.is_loaded = False
        logger.info("✅ HybridImageService cleanup complete")

# Create global instance
hybrid_service = HybridImageService()
