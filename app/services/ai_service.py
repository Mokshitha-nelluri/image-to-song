"""
AI Service for image captioning using BLIP-2 model.
Optimized for production use with memory management and caching.
"""
import asyncio
import io
import time
import logging
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration

from ..core.config import settings
from ..utils.image_utils import ImageProcessor

# Set up logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

class BLIP2Service:
    """
    Production-optimized BLIP-2 image captioning service.
    
    Features:
    - Memory-efficient model loading with quantization
    - Async processing with thread pool
    - GPU utilization optimization
    - Model warm-up for consistent performance
    - Error handling and fallback strategies
    """
    
    def __init__(self):
        self.model: Optional[Blip2ForConditionalGeneration] = None
        self.processor: Optional[Blip2Processor] = None
        self.device = self._get_optimal_device()
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        self.is_model_loaded = False
        self.model_loading_lock = asyncio.Lock()
        
        logger.info(f"BLIP2Service initialized with device: {self.device}")
    
    def _get_optimal_device(self) -> torch.device:
        """Determine the best device for inference."""
        if settings.USE_GPU and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using GPU: {torch.cuda.get_device_name()}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = torch.device("mps")  # Apple Silicon
            logger.info("Using Apple Silicon GPU (MPS)")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU for inference")
        
        return device
    
    async def load_model(self) -> None:
        """
        Load BLIP-2 model with optimizations.
        This method is thread-safe and will only load the model once.
        """
        if self.is_model_loaded:
            return
        
        async with self.model_loading_lock:
            if self.is_model_loaded:  # Double-check after acquiring lock
                return
            
            logger.info("Loading BLIP-2 model...")
            start_time = time.time()
            
            try:
                # Load model in a separate thread to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._load_model_sync
                )
                
                # Warm up the model
                await self._warm_up_model()
                
                self.is_model_loaded = True
                load_time = time.time() - start_time
                logger.info(f"BLIP-2 model loaded successfully in {load_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Failed to load BLIP-2 model: {str(e)}")
                raise RuntimeError(f"Model loading failed: {str(e)}")
    
    def _load_model_sync(self) -> None:
        """Synchronous model loading with memory optimizations."""
        try:
            # Load processor first (lightweight)
            self.processor = Blip2Processor.from_pretrained(
                settings.BLIP2_MODEL_NAME,
                cache_dir=settings.MODEL_CACHE_DIR
            )
            
            # Model loading with optimizations
            model_kwargs = {
                "cache_dir": settings.MODEL_CACHE_DIR,
                "low_cpu_mem_usage": True,
                "torch_dtype": torch.float16 if self.device.type == "cuda" else torch.float32,
            }
            
            # Add GPU-specific optimizations
            if self.device.type == "cuda":
                model_kwargs.update({
                    "device_map": "auto",
                    "load_in_8bit": True,  # Quantization for memory efficiency
                })
            
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                settings.BLIP2_MODEL_NAME,
                **model_kwargs
            )
            
            # Move to device if not using device_map
            if "device_map" not in model_kwargs:
                self.model = self.model.to(self.device)
            
            # Set to evaluation mode
            self.model.eval()
            
            # Enable memory efficient attention if available
            if hasattr(self.model, 'enable_memory_efficient_attention'):
                self.model.enable_memory_efficient_attention()
            
            logger.info(f"Model loaded with dtype: {self.model.dtype}")
            
        except Exception as e:
            logger.error(f"Synchronous model loading failed: {str(e)}")
            raise
    
    async def _warm_up_model(self) -> None:
        """Warm up the model with a dummy image to ensure consistent performance."""
        logger.info("Warming up BLIP-2 model...")
        
        try:
            # Create a dummy white image
            dummy_image = Image.new('RGB', (384, 384), color='white')
            dummy_bytes = io.BytesIO()
            dummy_image.save(dummy_bytes, format='JPEG')
            dummy_bytes = dummy_bytes.getvalue()
            
            # Run inference to warm up
            await self.generate_caption(dummy_bytes, warm_up=True)
            logger.info("Model warm-up completed")
            
        except Exception as e:
            logger.warning(f"Model warm-up failed: {str(e)}")
    
    async def generate_caption(
        self, 
        image_bytes: bytes, 
        warm_up: bool = False,
        max_length: int = 50,
        num_beams: int = 3
    ) -> str:
        """
        Generate caption for an image asynchronously.
        
        Args:
            image_bytes: Raw image bytes
            warm_up: Whether this is a warm-up call
            max_length: Maximum caption length
            num_beams: Number of beams for beam search
            
        Returns:
            str: Generated caption
        """
        if not self.is_model_loaded:
            await self.load_model()
        
        try:
            # Preprocess image
            if not warm_up:
                processed_bytes = ImageProcessor.preprocess_for_blip2(image_bytes)
            else:
                processed_bytes = image_bytes
            
            # Run inference in thread pool
            caption = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._generate_caption_sync,
                processed_bytes,
                max_length,
                num_beams
            )
            
            if not warm_up:
                logger.info(f"Generated caption: {caption[:100]}...")
            
            return caption
            
        except Exception as e:
            logger.error(f"Caption generation failed: {str(e)}")
            return self._get_fallback_caption()
    
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
            inputs = self.processor(
                image, 
                return_tensors="pt"
            ).to(self.device)
            
            # Handle different dtypes
            if self.device.type == "cuda" and self.model.dtype == torch.float16:
                inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                    do_sample=False  # Deterministic output
                )
            
            # Decode caption
            caption = self.processor.decode(
                generated_ids[0], 
                skip_special_tokens=True
            ).strip()
            
            # Clean up GPU memory
            del inputs, generated_ids
            if self.device.type == "cuda":
                torch.cuda.empty_cache()
            
            return caption if caption else "An image"
            
        except Exception as e:
            logger.error(f"Synchronous caption generation failed: {str(e)}")
            raise
    
    def _get_fallback_caption(self) -> str:
        """Return a fallback caption when generation fails."""
        return "Unable to generate description for this image"
    
    async def batch_generate_captions(
        self, 
        image_bytes_list: list[bytes], 
        max_length: int = 50
    ) -> list[str]:
        """
        Generate captions for multiple images in batch.
        
        Args:
            image_bytes_list: List of image bytes
            max_length: Maximum caption length
            
        Returns:
            list[str]: List of generated captions
        """
        if not self.is_model_loaded:
            await self.load_model()
        
        # Process images in batches to manage memory
        batch_size = min(settings.MAX_BATCH_SIZE, len(image_bytes_list))
        results = []
        
        for i in range(0, len(image_bytes_list), batch_size):
            batch = image_bytes_list[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [
                self.generate_caption(img_bytes, max_length=max_length) 
                for img_bytes in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in batch results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch caption generation failed: {str(result)}")
                    results.append(self._get_fallback_caption())
                else:
                    results.append(result)
        
        return results
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_model_loaded:
            return {"status": "not_loaded"}
        
        info = {
            "status": "loaded",
            "model_name": settings.BLIP2_MODEL_NAME,
            "device": str(self.device),
            "dtype": str(self.model.dtype) if self.model else "unknown",
        }
        
        if self.device.type == "cuda":
            info.update({
                "gpu_name": torch.cuda.get_device_name(),
                "gpu_memory_allocated": f"{torch.cuda.memory_allocated() / 1e9:.2f} GB",
                "gpu_memory_cached": f"{torch.cuda.memory_reserved() / 1e9:.2f} GB"
            })
        
        return info
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.model:
            del self.model
            self.model = None
        
        if self.processor:
            del self.processor
            self.processor = None
        
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
        
        self.executor.shutdown(wait=True)
        self.is_model_loaded = False
        
        logger.info("BLIP2Service cleaned up")

# Global service instance
blip2_service = BLIP2Service()

@asynccontextmanager
async def get_blip2_service():
    """Context manager for BLIP-2 service."""
    try:
        await blip2_service.load_model()
        yield blip2_service
    finally:
        # Service cleanup is handled by the application lifecycle
        pass
