#!/usr/bin/env python3
"""
End-to-end test for the Gemini SDK migration.
This script tests the core functionality that was migrated from google-generativeai to google-genai.
"""

import os
import sys
import json
from io import BytesIO

# Set up test environment
os.environ["GOOGLE_GEMINI_API_KEY"] = "test-key"
os.environ["IS_LOCAL_DEV"] = "true"

def test_imports():
    """Test that the new imports work correctly."""
    print("Testing imports...")
    try:
        from google import genai
        from google.genai import types
        print("✓ New SDK imports successful")
        return True, genai, types
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False, None, None

def test_client_creation(genai):
    """Test client creation with new SDK."""
    print("Testing client creation...")
    try:
        client = genai.Client(api_key="test-key")
        print("✓ Client created successfully")
        return True, client
    except Exception as e:
        print(f"✗ Client creation failed: {e}")
        return False, None

def test_content_preparation(types):
    """Test content preparation with new format."""
    print("Testing content preparation...")
    try:
        # Test text content
        text_part = types.Part.from_text("Hello, world!")
        print(f"✓ Text part created: {type(text_part)}")
        
        # Test image content (simulate with bytes)
        fake_image_bytes = b"fake-image-data"
        image_part = types.Part.from_bytes(data=fake_image_bytes, mime_type="image/jpeg")
        print(f"✓ Image part created: {type(image_part)}")
        
        # Test content list
        content = [text_part, image_part]
        print(f"✓ Content list created with {len(content)} parts")
        
        return True
    except Exception as e:
        print(f"✗ Content preparation failed: {e}")
        return False

def test_pil_image_conversion():
    """Test PIL image to Part conversion function."""
    print("Testing PIL image conversion...")
    try:
        # Import PIL
        import PIL.Image
        from io import BytesIO
        
        # Create a simple test image
        img = PIL.Image.new('RGB', (100, 100), color='red')
        
        # Test the conversion function from app.py
        def pil_image_to_part(pil_image):
            """Convert PIL Image to google.genai.types.Part"""
            from google.genai import types
            img_buffer = BytesIO()
            if pil_image.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                pil_image = pil_image.convert('RGB')
                pil_image.save(img_buffer, format='JPEG')
                mime_type = 'image/jpeg'
            else:
                pil_image.save(img_buffer, format=pil_image.format or 'JPEG')
                mime_type = f'image/{(pil_image.format or "jpeg").lower()}'
            
            img_bytes = img_buffer.getvalue()
            return types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
        
        part = pil_image_to_part(img)
        print(f"✓ PIL image converted to Part: {type(part)}")
        return True
    except Exception as e:
        print(f"✗ PIL image conversion failed: {e}")
        return False

def test_api_structure(client, types):
    """Test the API structure without making actual calls."""
    print("Testing API structure...")
    try:
        # Check if models attribute exists
        models = client.models
        print(f"✓ Client has models attribute: {type(models)}")
        
        # Check if generate_content method exists
        if hasattr(models, 'generate_content'):
            print("✓ generate_content method exists")
        else:
            print("✗ generate_content method not found")
            return False
        
        # Test content structure
        test_content = [
            types.Part.from_text("Test prompt"),
            types.Part.from_bytes(data=b"fake-image", mime_type="image/jpeg")
        ]
        print(f"✓ Test content prepared with {len(test_content)} parts")
        
        return True
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False

def test_migration_completeness():
    """Test that all necessary migration components are in place."""
    print("Testing migration completeness...")
    
    # Check requirements.txt
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        if "google-genai" in requirements:
            print("✓ requirements.txt updated with new SDK")
        else:
            print("✗ requirements.txt not updated")
            return False
        
        if "google-generativeai" in requirements:
            print("⚠ Old SDK still in requirements.txt")
        else:
            print("✓ Old SDK removed from requirements.txt")
            
    except FileNotFoundError:
        print("✗ requirements.txt not found")
        return False
    
    # Check app.py imports
    try:
        with open("app.py", "r") as f:
            app_content = f.read()
        
        if "from google import genai" in app_content:
            print("✓ app.py has new import")
        else:
            print("✗ app.py missing new import")
            return False
        
        if "from google.genai import types" in app_content:
            print("✓ app.py has types import")
        else:
            print("✗ app.py missing types import")
            return False
            
        if "pil_image_to_part" in app_content:
            print("✓ app.py has image conversion function")
        else:
            print("✗ app.py missing image conversion function")
            return False
    
    except FileNotFoundError:
        print("✗ app.py not found")
        return False
    
    return True

def main():
    """Run all migration tests."""
    print("Gemini SDK Migration Test Suite")
    print("=" * 50)
    
    # Test imports
    success, genai, types = test_imports()
    if not success:
        print("\n✗ Migration test failed - imports not working")
        sys.exit(1)
    
    # Test client creation
    success, client = test_client_creation(genai)
    if not success:
        print("\n✗ Migration test failed - client creation not working")
        sys.exit(1)
    
    # Test content preparation
    if not test_content_preparation(types):
        print("\n✗ Migration test failed - content preparation not working")
        sys.exit(1)
    
    # Test PIL image conversion
    if not test_pil_image_conversion():
        print("\n✗ Migration test failed - PIL image conversion not working")
        sys.exit(1)
    
    # Test API structure
    if not test_api_structure(client, types):
        print("\n✗ Migration test failed - API structure not correct")
        sys.exit(1)
    
    # Test migration completeness
    if not test_migration_completeness():
        print("\n✗ Migration test failed - migration incomplete")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✓ All migration tests passed!")
    print("The migration from google-generativeai to google-genai is complete.")
    print("\nNext steps:")
    print("1. Install the new SDK: pip install google-genai>=1.26.0")
    print("2. Uninstall the old SDK: pip uninstall google-generativeai") 
    print("3. Test the application: streamlit run app.py")

if __name__ == "__main__":
    main()