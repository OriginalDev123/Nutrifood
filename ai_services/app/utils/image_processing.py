"""
Image Processing Utilities - NutriAI Vision
Compress và validate images trước khi gửi cho Gemini
"""

from PIL import Image
import io
import logging
from pathlib import Path
from typing import Tuple, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Xử lý ảnh: validation, compression, cleanup
    
    Mục tiêu:
    1. Giảm kích thước file (tiết kiệm bandwidth + Gemini tokens)
    2. Chuẩn hóa format (JPEG)
    3. Validate ảnh hợp lệ
    """
    
    # Các format được phép
    ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    @staticmethod
    def validate_image(file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate file có phải ảnh hợp lệ không
        
        Args:
            file_path: Đường dẫn file cần validate
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Kiểm tra file tồn tại
            if not file_path.exists():
                return False, "File không tồn tại"
            
            # Kiểm tra kích thước file
            file_size = file_path.stat().st_size
            if file_size > settings.max_image_size_bytes:
                max_mb = settings.MAX_IMAGE_SIZE_MB
                actual_mb = file_size / (1024 * 1024)
                return False, f"File quá lớn ({actual_mb:.1f}MB). Tối đa {max_mb}MB"
            
            # Kiểm tra extension
            if file_path.suffix.lower() not in ImageProcessor.ALLOWED_EXTENSIONS:
                return False, f"Format không hỗ trợ. Chỉ chấp nhận: {', '.join(ImageProcessor.ALLOWED_EXTENSIONS)}"
            
            # Thử mở ảnh bằng PIL (để verify không corrupt)
            with Image.open(file_path) as img:
                # Verify format
                if img.format not in ImageProcessor.ALLOWED_FORMATS:
                    return False, f"Format {img.format} không được hỗ trợ"
                
                # Verify có thể đọc được
                img.verify()
            
            return True, None
            
        except Exception as e:
            logger.error(f"Lỗi validate image: {str(e)}")
            return False, f"File không phải ảnh hợp lệ: {str(e)}"
    
    @staticmethod
    def compress_image(input_path: Path, output_path: Path) -> dict:
        """
        Nén ảnh để gửi Gemini (tiết kiệm tokens)
        
        Process:
        1. Resize về TARGET_IMAGE_SIZE_PX (giữ tỉ lệ)
        2. Convert sang RGB (nếu cần)
        3. Save dạng JPEG với quality setting
        
        Args:
            input_path: Ảnh gốc
            output_path: Ảnh đã nén
        
        Returns:
            dict chứa metadata (original_size, compressed_size, ...)
        """
        try:
            with Image.open(input_path) as img:
                # Lưu thông tin gốc
                original_format = img.format
                original_size = img.size
                original_file_size = input_path.stat().st_size
                
                logger.info(
                    f"📸 Ảnh gốc: {original_size[0]}x{original_size[1]}, "
                    f"format={original_format}, size={original_file_size/1024:.1f}KB"
                )
                
                # === BƯỚC 1: Convert sang RGB (cần cho JPEG) ===
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Tạo background trắng
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    
                    # Paste ảnh lên background (giữ transparency)
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # === BƯỚC 2: Resize (giữ aspect ratio) ===
                max_size = settings.TARGET_IMAGE_SIZE_PX
                width, height = img.size
                
                # Tính kích thước mới (giữ tỉ lệ)
                if width > max_size or height > max_size:
                    if width > height:
                        new_width = max_size
                        new_height = int(height * (max_size / width))
                    else:
                        new_height = max_size
                        new_width = int(width * (max_size / height))
                    
                    # Resize với LANCZOS (chất lượng cao)
                    img = img.resize(
                        (new_width, new_height),
                        Image.Resampling.LANCZOS
                    )
                    
                    logger.info(f"🔄 Resize: {width}x{height} → {new_width}x{new_height}")
                
                # === BƯỚC 3: Save dạng JPEG với compression ===
                img.save(
                    output_path,
                    format='JPEG',
                    quality=settings.IMAGE_QUALITY,
                    optimize=True  # Tối ưu thêm
                )
                
                # Tính toán metadata
                compressed_file_size = output_path.stat().st_size
                compression_ratio = 1 - (compressed_file_size / original_file_size)
                
                metadata = {
                    "original_size": original_size,
                    "compressed_size": img.size,
                    "original_format": original_format,
                    "compressed_format": "JPEG",
                    "original_size_kb": round(original_file_size / 1024, 1),
                    "compressed_size_kb": round(compressed_file_size / 1024, 1),
                    "compression_ratio": round(compression_ratio * 100, 1),  # %
                    "saved_kb": round((original_file_size - compressed_file_size) / 1024, 1)
                }
                
                logger.info(
                    f"✅ Nén thành công: {metadata['original_size_kb']}KB → "
                    f"{metadata['compressed_size_kb']}KB "
                    f"(giảm {metadata['compression_ratio']}%)"
                )
                
                return metadata
                
        except Exception as e:
            logger.error(f"❌ Lỗi nén ảnh: {str(e)}", exc_info=True)
            raise ValueError(f"Không thể nén ảnh: {str(e)}")


# Singleton instance
image_processor = ImageProcessor()