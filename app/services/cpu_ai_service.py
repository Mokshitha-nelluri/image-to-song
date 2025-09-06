"""
CPU-Optimized AI Service for testing.
This version loads a smaller model or uses optimizations for better CPU performance.
"""
import asyncio
import io
import time
import logging
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

from app.core.config import settings
from app.utils.image_utils import ImageProcessor

# Set up logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

class CPUOptimizedCaptionService:
    """
    CPU-optimized image captioning service using smaller BLIP model.
    Uses the original BLIP model which is smaller and faster than BLIP-2.
    """
    
    def __init__(self):
        self.model: Optional[BlipForConditionalGeneration] = None
        self.processor: Optional[BlipProcessor] = None
        self.device = torch.device("cpu")  # Force CPU for consistency
        self.executor = ThreadPoolExecutor(max_workers=1)  # Single thread for CPU
        self.is_model_loaded = False
        self.model_loading_lock = asyncio.Lock()
        
        # Use smaller, faster model
        self.model_name = "Salesforce/blip-image-captioning-base"  # ~1GB vs 15GB
        
        logger.info(f"CPUOptimizedCaptionService initialized with device: {self.device}")
        logger.info(f"Using smaller model: {self.model_name}")
    
    async def load_model(self) -> None:
        """Load the smaller BLIP model for CPU inference."""
        if self.is_model_loaded:
            return
        
        async with self.model_loading_lock:
            if self.is_model_loaded:
                return
            
            logger.info("Loading CPU-optimized BLIP model...")
            start_time = time.time()
            
            try:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._load_model_sync
                )
                
                self.is_model_loaded = True
                load_time = time.time() - start_time
                logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
                raise RuntimeError(f"Model loading failed: {str(e)}")
    
    def _load_model_sync(self) -> None:
        """Synchronous model loading."""
        try:
            # Load processor
            self.processor = BlipProcessor.from_pretrained(
                self.model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            )
            
            # Load model with CPU optimizations
            self.model = BlipForConditionalGeneration.from_pretrained(
                self.model_name,
                cache_dir=settings.MODEL_CACHE_DIR,
                torch_dtype=torch.float32,  # Use float32 for CPU
                low_cpu_mem_usage=True
            )
            
            self.model = self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Model loaded with dtype: {self.model.dtype}")
            
        except Exception as e:
            logger.error(f"Synchronous model loading failed: {str(e)}")
            raise
    
    async def generate_caption(
        self, 
        image_bytes: bytes, 
        max_length: int = 30,  # Shorter for faster generation
        num_beams: int = 2     # Fewer beams for speed
    ) -> str:
        """Generate caption with CPU optimizations."""
        if not self.is_model_loaded:
            await self.load_model()
        
        try:
            # Preprocess image
            processed_bytes = ImageProcessor.preprocess_for_blip2(image_bytes)
            
            # Run inference
            caption = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._generate_caption_sync,
                processed_bytes,
                max_length,
                num_beams
            )
            
            logger.info(f"Generated caption: {caption}")
            return caption
            
        except Exception as e:
            logger.error(f"Caption generation failed: {str(e)}")
            return "Unable to generate description for this image"
    
    def _generate_caption_sync(
        self, 
        image_bytes: bytes, 
        max_length: int, 
        num_beams: int
    ) -> str:
        """Synchronous caption generation."""
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Process inputs
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Generate with optimizations
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode
            caption = self.processor.decode(
                generated_ids[0], 
                skip_special_tokens=True
            ).strip()
            
            return caption if caption else "An image"
            
        except Exception as e:
            logger.error(f"Synchronous caption generation failed: {str(e)}")
            raise
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        if not self.is_model_loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_name": self.model_name,
            "device": str(self.device),
            "dtype": str(self.model.dtype) if self.model else "unknown",
            "optimization": "CPU-optimized smaller model"
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.model:
            del self.model
            self.model = None
        
        if self.processor:
            del self.processor
            self.processor = None
        
        self.executor.shutdown(wait=True)
        self.is_model_loaded = False
        
        logger.info("CPUOptimizedCaptionService cleaned up")

# Global service instance
cpu_caption_service = CPUOptimizedCaptionService()
