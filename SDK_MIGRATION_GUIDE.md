# Gemini SDK Migration Guide

This document describes the migration from the deprecated `google-generativeai` SDK to the new `google-genai` SDK.

## Overview

The repository has been updated to use the new Google Gemini Gen AI SDK as the previous SDK has been deprecated. This migration ensures continued compatibility and access to the latest features.

## Changes Made

### 1. Package Dependency Update

**Before:**
```
google-generativeai>=0.3.0
```

**After:**
```
google-genai>=1.26.0
```

### 2. Import Changes

**Before:**
```python
import google.generativeai as genai
```

**After:**
```python
from google import genai
from google.genai import types
```

### 3. Client Configuration

**Before:**
```python
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
```

**After:**
```python
client = genai.Client(api_key=api_key)
model_name = "gemini-2.0-flash"
```

### 4. Content Generation

**Before:**
```python
response = model.generate_content(content)
response.resolve()  # Wait for completion
text = response.text
```

**After:**
```python
response = client.models.generate_content(
    model=model_name,
    contents=content
)
text = response.text  # No need to resolve
```

### 5. Image Handling

**Before:**
```python
# PIL Images could be passed directly
content = [prompt_text, pil_image, user_prompt]
```

**After:**
```python
# PIL Images must be converted to types.Part
def pil_image_to_part(pil_image):
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

content = [
    types.Part.from_text(prompt_text),
    pil_image_to_part(pil_image),
    types.Part.from_text(user_prompt)
]
```

### 6. Content Preparation

**Before:**
```python
content = [
    system_prompt,  # String
    image,          # PIL Image
    user_prompt     # String
]
```

**After:**
```python
content = [
    types.Part.from_text(system_prompt),
    pil_image_to_part(image),
    types.Part.from_text(user_prompt)
]
```

## Files Updated

1. **requirements.txt** - Updated package dependency
2. **app.py** - Updated imports, client configuration, and API calls
3. **Flashcard_Generation_LLM.ipynb** - Updated imports and configuration

## Installation Instructions

### For Development

1. Uninstall the old SDK:
   ```bash
   pip uninstall google-generativeai
   ```

2. Install the new SDK:
   ```bash
   pip install google-genai>=1.26.0
   ```

3. Install other dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

The environment variables remain the same:

```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
LLMWHISPERER_BASE_URL_V2=your_llmwhisperer_base_url
LLMWHISPERER_API_KEY=your_llmwhisperer_api_key
IS_LOCAL_DEV=true
```

## Testing the Migration

Run the application to verify the migration:

```bash
streamlit run app.py
```

## Compatibility Notes

- The new SDK provides the same core functionality
- Response objects no longer require `.resolve()` calls
- Image handling requires explicit conversion to `types.Part` objects
- Text content should be wrapped in `types.Part.from_text()`

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure the old SDK is uninstalled and new SDK is installed
2. **Image Conversion**: Ensure PIL images are converted using the `pil_image_to_part()` function
3. **Content Format**: Wrap strings in `types.Part.from_text()`

### Reverting if Needed

If you need to temporarily revert:

1. Restore the old requirements.txt entry:
   ```
   google-generativeai>=0.3.0
   ```

2. Revert the import and API changes in the Python files

## Migration Benefits

- Access to latest Gemini API features
- Better type safety with the new SDK
- Improved error handling
- Future-proof compatibility

## References

- [New SDK GitHub Repository](https://github.com/googleapis/python-genai)
- [Migration Guide](https://ai.google.dev/gemini-api/docs/migrate)
- [Deprecated SDK Repository](https://github.com/google-gemini/deprecated-generative-ai-python)