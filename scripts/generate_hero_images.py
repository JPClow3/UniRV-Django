#!/usr/bin/env python
"""
Generate responsive hero image variants from source image.

This script generates multiple widths (480, 768, 1024, 1600, 2400) in three formats:
- AVIF (modern, best compression)
- WebP (widely supported, good compression)
- JPEG (fallback, universal support)

Also generates a Low Quality Image Placeholder (LQIP) for instant display.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageFilter

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
SOURCE_IMAGE = PROJECT_ROOT / "static" / "img" / "agrohub-hero.webp"
OUTPUT_DIR = PROJECT_ROOT / "static" / "img" / "hero"
WIDTHS = [480, 768, 1024, 1600, 2400]
LQIP_SIZE = 40  # 40px width for LQIP
LQIP_BLUR = 10  # Blur radius for LQIP

# Quality settings
AVIF_QUALITY = 80
WEBP_QUALITY = 85
JPEG_QUALITY = 90


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def generate_variants(source_path, output_dir, widths, formats):
    """Generate image variants in multiple widths and formats."""
    if not source_path.exists():
        raise FileNotFoundError(f"Source image not found: {source_path}")
    
    print(f"Loading source image: {source_path}")
    with Image.open(source_path) as img:
        # Convert to RGB if necessary (for JPEG/AVIF)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        original_width, original_height = img.size
        aspect_ratio = original_height / original_width
        
        print(f"Original size: {original_width}x{original_height} (aspect ratio: {aspect_ratio:.3f})")
        
        generated = []
        
        for width in widths:
            height = int(width * aspect_ratio)
            print(f"\nGenerating {width}w variants...")
            
            # Resize image
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            for format_name, format_ext, save_kwargs in formats:
                output_path = output_dir / f"agrohub-hero-{width}w.{format_ext}"
                
                try:
                    if format_name == 'AVIF':
                        resized.save(output_path, format='AVIF', quality=AVIF_QUALITY, **save_kwargs)
                    elif format_name == 'WEBP':
                        resized.save(output_path, format='WEBP', quality=WEBP_QUALITY, **save_kwargs)
                    elif format_name == 'JPEG':
                        resized.save(output_path, format='JPEG', quality=JPEG_QUALITY, optimize=True, **save_kwargs)
                    
                    file_size = output_path.stat().st_size
                    print(f"  ✓ {format_ext:6} {width:4}w: {file_size:>8,} bytes ({output_path.name})")
                    generated.append(output_path)
                except Exception as e:
                    print(f"  ✗ {format_ext:6} {width:4}w: Failed - {e}")
        
        return generated


def generate_lqip(source_path, output_dir, size, blur_radius):
    """Generate Low Quality Image Placeholder (LQIP)."""
    if not source_path.exists():
        raise FileNotFoundError(f"Source image not found: {source_path}")
    
    print(f"\nGenerating LQIP ({size}px, blur={blur_radius})...")
    
    with Image.open(source_path) as img:
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate height maintaining aspect ratio
        aspect_ratio = img.height / img.width
        lqip_height = int(size * aspect_ratio)
        
        # Resize to tiny size
        tiny = img.resize((size, lqip_height), Image.Resampling.LANCZOS)
        
        # Apply blur
        blurred = tiny.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # Save as JPEG with low quality
        output_path = output_dir / "agrohub-hero-lqip.jpg"
        blurred.save(output_path, format='JPEG', quality=30, optimize=True)
        
        file_size = output_path.stat().st_size
        print(f"  ✓ LQIP: {file_size:>8,} bytes ({output_path.name})")
        
        return output_path


def main():
    """Main execution function."""
    print("=" * 60)
    print("Hero Image Variant Generator")
    print("=" * 60)
    
    try:
        ensure_output_dir()
        
        # Define formats: (name, extension, save_kwargs)
        formats = [
            ('AVIF', 'avif', {}),
            ('WEBP', 'webp', {'method': 6}),  # method 6 = best quality, slower
            ('JPEG', 'jpg', {}),
        ]
        
        # Generate variants
        generated = generate_variants(SOURCE_IMAGE, OUTPUT_DIR, WIDTHS, formats)
        
        # Generate LQIP
        lqip_path = generate_lqip(SOURCE_IMAGE, OUTPUT_DIR, LQIP_SIZE, LQIP_BLUR)
        
        print("\n" + "=" * 60)
        print(f"✓ Successfully generated {len(generated)} image variants")
        print(f"✓ Generated LQIP placeholder")
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        print(f"\nPlease ensure the source image exists at: {SOURCE_IMAGE}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

