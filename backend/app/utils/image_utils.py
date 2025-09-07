"""
Image processing utilities for the Image-to-Song application.
Handles image validation, compression, and preprocessing.
"""
import io
import hashlib
from typing import Tuple, Optional
from PIL import Image, ImageOps
import cv2
import numpy as np

from ..core.config import settings

class ImageProcessor:
    """Handles all image processing operations with optimization for BLIP-2."""
    
    @staticmethod
    def validate_image(image_bytes: bytes) -> bool:
        """
        Validate if the image bytes represent a valid image.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            bool: True if valid image, False otherwise
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()  # Verify image integrity
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_image_info(image_bytes: bytes) -> dict:
        """
        Extract basic information about the image.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            dict: Image information including size, format, mode
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return {
                "size": image.size,
                "format": image.format,
                "mode": image.mode,
                "width": image.width,
                "height": image.height,
                "file_size": len(image_bytes)
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def calculate_image_hash(image_bytes: bytes) -> str:
        """
        Calculate SHA-256 hash of image bytes for caching.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            str: Hexadecimal hash string
        """
        return hashlib.sha256(image_bytes).hexdigest()
    
    @staticmethod
    def preprocess_for_blip2(image_bytes: bytes) -> bytes:
        """
        Preprocess image for optimal BLIP-2 inference.
        - Resize to target dimensions
        - Convert to RGB
        - Optimize quality
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            bytes: Preprocessed image bytes
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Auto-orient based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Resize to BLIP-2 optimal size while maintaining aspect ratio
            image = ImageProcessor._smart_resize(image, settings.TARGET_IMAGE_SIZE)
            
            # Save to bytes with optimized quality
            output_buffer = io.BytesIO()
            image.save(
                output_buffer, 
                format='JPEG', 
                quality=85,  # Good balance of quality vs size
                optimize=True
            )
            
            return output_buffer.getvalue()
            
        except Exception as e:
            raise ValueError(f"Image preprocessing failed: {str(e)}")
    
    @staticmethod
    def _smart_resize(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize image intelligently maintaining aspect ratio.
        
        Args:
            image: PIL Image object
            target_size: Target (width, height)
            
        Returns:
            Image.Image: Resized image
        """
        target_width, target_height = target_size
        original_width, original_height = image.size
        
        # Calculate ratios
        width_ratio = target_width / original_width
        height_ratio = target_height / original_height
        
        # Use the smaller ratio to maintain aspect ratio
        ratio = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # Resize using high-quality resampling
        resized_image = image.resize(
            (new_width, new_height), 
            Image.Resampling.LANCZOS
        )
        
        # Create a new image with target dimensions and paste the resized image
        final_image = Image.new('RGB', target_size, (255, 255, 255))  # White background
        
        # Calculate position to center the image
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        
        final_image.paste(resized_image, (x_offset, y_offset))
        
        return final_image
    
    @staticmethod
    def compress_image(image_bytes: bytes, max_size_mb: float = 2.0) -> bytes:
        """
        Compress image to stay within size limit while maintaining quality.
        
        Args:
            image_bytes: Raw image bytes
            max_size_mb: Maximum size in megabytes
            
        Returns:
            bytes: Compressed image bytes
        """
        max_size_bytes = int(max_size_mb * 1024 * 1024)
        
        if len(image_bytes) <= max_size_bytes:
            return image_bytes
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Try different quality levels
            for quality in [85, 75, 65, 55, 45]:
                output_buffer = io.BytesIO()
                image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                compressed_bytes = output_buffer.getvalue()
                
                if len(compressed_bytes) <= max_size_bytes:
                    return compressed_bytes
            
            # If still too large, resize the image
            scale_factor = (max_size_bytes / len(image_bytes)) ** 0.5
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            output_buffer = io.BytesIO()
            resized_image.save(output_buffer, format='JPEG', quality=75, optimize=True)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            raise ValueError(f"Image compression failed: {str(e)}")
    
    @staticmethod
    def extract_dominant_colors(image_bytes: bytes, num_colors: int = 5) -> list:
        """
        Extract dominant colors from the image for mood analysis.
        
        Args:
            image_bytes: Raw image bytes
            num_colors: Number of dominant colors to extract
            
        Returns:
            list: List of dominant colors as RGB tuples
        """
        try:
            # Convert bytes to OpenCV format
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Reshape image to be a list of pixels
            pixels = image.reshape(-1, 3)
            
            # Use K-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Get the colors
            colors = kmeans.cluster_centers_.astype(int)
            
            # Calculate color percentages
            labels = kmeans.labels_
            percentages = [(labels == i).sum() / len(labels) for i in range(num_colors)]
            
            # Combine colors with their percentages
            color_data = [
                {
                    "rgb": (int(color[0]), int(color[1]), int(color[2])),
                    "hex": f"#{int(color[0]):02x}{int(color[1]):02x}{int(color[2]):02x}",
                    "percentage": float(percentage)
                }
                for color, percentage in zip(colors, percentages)
            ]
            
            # Sort by percentage (most dominant first)
            color_data.sort(key=lambda x: x["percentage"], reverse=True)
            
            return color_data
            
        except Exception as e:
            # Fallback: return basic color analysis
            return ImageProcessor._basic_color_analysis(image_bytes)
    
    @staticmethod
    def _basic_color_analysis(image_bytes: bytes) -> list:
        """
        Basic color analysis fallback when advanced methods fail.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            list: Basic color information
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert('RGB')
            
            # Sample pixels from different regions
            width, height = image.size
            sample_points = [
                (width//4, height//4),
                (3*width//4, height//4),
                (width//2, height//2),
                (width//4, 3*height//4),
                (3*width//4, 3*height//4)
            ]
            
            colors = []
            for x, y in sample_points:
                rgb = image.getpixel((x, y))
                colors.append({
                    "rgb": rgb,
                    "hex": f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                    "percentage": 0.2  # Equal distribution
                })
            
            return colors
            
        except Exception:
            # Ultimate fallback
            return [{"rgb": (128, 128, 128), "hex": "#808080", "percentage": 1.0}]
