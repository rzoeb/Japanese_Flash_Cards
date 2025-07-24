# Building a Streamlit UI for code in 'Flashcard_Generation_LLM.ipynb'
# Importing the required libraries
import streamlit as st
from google import genai
from google.genai import types as google_types
from google.api_core import exceptions as google_exceptions
import PIL.Image
from PIL import ImageOps
import json
from unstract.llmwhisperer import LLMWhispererClientV2
import os
from io import BytesIO
from dotenv import load_dotenv
import base64
import logging
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from typing import List
import time

# Importing all variables from LLM_Prompts.py
from LLM_Prompts import *

# Pydantic Response Schemas
class SuitabilityResponse(BaseModel):
    is_suitable: str = Field(..., description="Yes or No")
    reason: str = Field(..., description="Brief explanation for the decision")

class FlashcardEntry(BaseModel):
    kanji: str = Field(..., description='Word in Kanji or Hiragana/Katakana (wrapped in double quotes)')
    furigana: str = Field(..., description='Phonetic reading in Hiragana (wrapped in double quotes)')
    english_translation_and_notes: str = Field(..., description='English translation with usage notes (wrapped in double quotes)')

class FlashcardResponse(BaseModel):
    flashcards: List[FlashcardEntry] = Field(..., description="List of generated flashcards")

class KanjiFlashcardEntry(BaseModel):
    kanji: str = Field(..., description='Individual Kanji character(s)')
    readings: str = Field(..., description='On-yomi and Kun-yomi readings separated by " | "')
    english_translation_and_notes: str = Field(..., description='English meanings and usage notes')
    example_words_and_sentences: str = Field(..., description='Example words and sentences using the Kanji')

class KanjiFlashcardResponse(BaseModel):
    flashcards: List[KanjiFlashcardEntry] = Field(..., description="List of generated Kanji flashcards")

# Load model information for configuration
def load_model_config():
    """Load model configuration from model_information.json"""
    try:
        with open("model_information.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load model_information.json: {e}")
        raise

# Setup console logger
def setup_console_logger():
    """Setup console-only logger for API usage tracking"""
    logger = logging.getLogger("flashcard_generator")
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to prevent duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Add a single StreamHandler
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid additional duplicates
    logger.propagate = False
    
    return logger

# Convert Pydantic FlashcardResponse to CSV format
def convert_flashcard_response_to_csv(flashcard_response):
    """Convert FlashcardResponse or KanjiFlashcardResponse to CSV format with proper quote wrapping"""
    csv_lines = []
    
    # Check if it's a KanjiFlashcardResponse or regular FlashcardResponse
    if hasattr(flashcard_response.flashcards[0], 'readings') if flashcard_response.flashcards else False:
        # Kanji flashcard format: Kanji, Readings, English Translation and Notes, Example Words and Sentences
        for entry in flashcard_response.flashcards:
            kanji = f'"{entry.kanji.replace(chr(34), chr(34)+chr(34))}"'
            readings = f'"{entry.readings.replace(chr(34), chr(34)+chr(34))}"'
            english = f'"{entry.english_translation_and_notes.replace(chr(34), chr(34)+chr(34))}"'
            examples = f'"{entry.example_words_and_sentences.replace(chr(34), chr(34)+chr(34))}"'
            csv_lines.append(f"{kanji},{readings},{english},{examples}")
    else:
        # Regular vocabulary flashcard format: Kanji, Furigana, English Translation and Notes
        for entry in flashcard_response.flashcards:
            kanji = f'"{entry.kanji.replace(chr(34), chr(34)+chr(34))}"'
            furigana = f'"{entry.furigana.replace(chr(34), chr(34)+chr(34))}"'
            english = f'"{entry.english_translation_and_notes.replace(chr(34), chr(34)+chr(34))}"'
            csv_lines.append(f"{kanji},{furigana},{english}")
    
    return "\n".join(csv_lines)

# Retry logic for API errors
def should_retry_api_call(exception):
    """Determine if API call should be retried based on exception type"""
    retryable_exceptions = [
        google_exceptions.ResourceExhausted,
        google_exceptions.ServiceUnavailable, 
        google_exceptions.InternalServerError,
        google_exceptions.DeadlineExceeded
    ]
    
    if isinstance(exception, tuple(retryable_exceptions)):
        return True
        
    # Check status codes
    if hasattr(exception, 'code'):
        retryable_codes = [8, 13, 14, 4]  # gRPC codes for rate limit, internal, unavailable, deadline
        return exception.code in retryable_codes
    
    return False

retry_on_api_error = retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception(should_retry_api_call)
)

# Image preprocessing function from unstract_multiple_llm_text_image.py
def preprocess_image(image, provider_list, logger, image_requirements_config):
    """
    Resizes, converts, and formats a PIL image based on the strictest requirements
    of the specified generator and evaluator model providers.
    """
    logger.info("--- Starting Image Preprocessing ---")
    try:
        # Get requirements for all providers in "provider_list"
        provider_requirements = []
        for provider in provider_list:
            req = image_requirements_config.get(provider, {})
            provider_requirements.append(req)

        # Determine the strictest requirements (ignore None values)
        max_size_mb_candidates = [req.get('max_size_mb', 1000) for req in provider_requirements if req.get('max_size_mb', 1000) is not None]
        max_size_mb = min(max_size_mb_candidates) if max_size_mb_candidates else 1000

        max_pixels_candidates = [req.get('max_pixels', float('inf')) for req in provider_requirements if req.get('max_pixels', float('inf')) is not None]
        max_pixels = min(max_pixels_candidates) if max_pixels_candidates else float('inf')

        max_edge_candidates = [req.get('max_edge', float('inf')) for req in provider_requirements if req.get('max_edge', float('inf')) is not None]
        max_edge = min(max_edge_candidates) if max_edge_candidates else float('inf')

        # Setting the required image format and media_type ('base64' and 'image/png')
        required_format = 'base64'
        media_type = 'image/png'

        # Reducing "max_size_mb" by 30% to account for base64 encoding overhead (minimum 1MB)
        max_size_mb = max(1, int(max_size_mb * 0.7))

        logger.info(f"Target constraints: max_pixels={max_pixels if max_pixels != float('inf') else 'None'}, max_size_mb={max_size_mb}, max_edge={max_edge if max_edge != float('inf') else 'None'}, format={required_format}, media_type={media_type}")

        img_copy = image.copy()

        # --- Handle Non-RGB/RGBA Modes ---
        if img_copy.mode not in ('RGB', 'RGBA'):
            logger.warning(f"Input image mode is '{img_copy.mode}'. Converting to 'RGB' for compatibility.")
            print(f"WARN: Converting image mode '{img_copy.mode}' to 'RGB'.")
            try:
                img_copy = img_copy.convert('RGB')
            except Exception as convert_e:
                logger.error(f"Failed to convert image mode from {img_copy.mode} to RGB: {convert_e}", exc_info=True)
                print(f"ERROR: Failed to convert image mode: {convert_e}")
                return None

        # --- Ensure Correct Orientation ---
        try:
            img_copy = ImageOps.exif_transpose(img_copy)
            logger.info("Applied EXIF transpose for orientation.")
        except Exception as exif_err:
            logger.warning(f"Could not apply EXIF transpose: {exif_err}")
            print(f"WARN: Could not apply EXIF transpose: {exif_err}")

        # --- Resizing Logic (Pixels, Edge, File Size) ---
        width, height = img_copy.size
        logger.info(f"Original dimensions (after potential mode conversion/transpose): {width}x{height}")

        # Resize based on Max Edge
        if width > max_edge or height > max_edge:
             logger.info(f"Resizing image to fit within max edge: {max_edge}px")
             img_copy.thumbnail((max_edge, max_edge), PIL.Image.LANCZOS)
             width, height = img_copy.size
             logger.info(f"Resized dimensions (max edge): {width}x{height}")

        # Resize based on Pixel Count
        pixel_count = width * height
        if pixel_count > max_pixels:
             scale_factor = (max_pixels / pixel_count) ** 0.5
             new_width = max(1, int(width * scale_factor))
             new_height = max(1, int(height * scale_factor))
             logger.info(f"Resizing image due to pixel count ({pixel_count:,} > {max_pixels:,}). New target: {new_width}x{new_height}")
             img_copy = img_copy.resize((new_width, new_height), PIL.Image.LANCZOS)
             width, height = img_copy.size
             logger.info(f"Resized dimensions (pixel count): {width}x{height}")

        # Resize based on File Size (Iterative)
        max_bytes = max_size_mb * 1024 * 1024
        temp_buffer = BytesIO()
        save_format = 'PNG' if media_type and 'png' in media_type.lower() else 'JPEG'
        logger.info(f"Checking size using format: {save_format}")
        quality = 95

        def get_image_size_bytes(img, buffer, fmt, qual=None):
            buffer.seek(0); buffer.truncate()
            save_kwargs = {'format': fmt}
            if fmt == 'PNG': save_kwargs['optimize'] = True
            if fmt == 'JPEG': save_kwargs['quality'] = qual if qual else 95
            img.save(buffer, **save_kwargs)
            return buffer.getbuffer().nbytes

        current_size_bytes = get_image_size_bytes(img_copy, temp_buffer, save_format, quality if save_format == 'JPEG' else None)
        logger.info(f"Initial size check ({save_format}): {current_size_bytes / (1024*1024):.2f}MB (Limit: {max_size_mb}MB)")

        iterations = 0
        max_resize_iterations = 7
        while current_size_bytes > max_bytes and iterations < max_resize_iterations:
            iterations += 1
            logger.warning(f"Image size ({current_size_bytes / (1024*1024):.2f}MB) exceeds limit ({max_size_mb}MB). Reducing size (Iteration {iterations}).")
            print(f"WARN: Image size too large, reducing... (Iteration {iterations})")

            width, height = img_copy.size
            scale_factor = 0.90
            new_width = max(1, int(width * scale_factor))
            new_height = max(1, int(height * scale_factor))

            if new_width == width and new_height == height:
                logger.warning("Cannot resize image further (minimum dimensions reached).")
                break

            logger.info(f"Resizing dimensions to {new_width}x{new_height}")
            img_copy = img_copy.resize((new_width, new_height), PIL.Image.LANCZOS)

            if save_format == 'JPEG':
                quality = max(70, quality - 5)
                logger.info(f"Reduced JPEG quality to {quality}")

            current_size_bytes = get_image_size_bytes(img_copy, temp_buffer, save_format, quality if save_format == 'JPEG' else None)
            logger.info(f"New size check: {current_size_bytes / (1024*1024):.2f}MB")

        # Final size check after loop
        if current_size_bytes > max_bytes:
             logger.error(f"Failed to reduce image size below {max_size_mb}MB after {iterations} iterations. Final size: {current_size_bytes / (1024*1024):.2f}MB")
             print(f"ERROR: Could not reduce image size sufficiently. Final size: {current_size_bytes / (1024*1024):.2f}MB")
             return None
        else:
             logger.info(f"Final image size: {current_size_bytes / (1024*1024):.2f}MB, dimensions: {img_copy.width}x{img_copy.height}")
             print(f"INFO: Image preprocessed. Final size: {current_size_bytes / (1024*1024):.2f}MB")

        # --- Final Conversion (Base64) ---
        if required_format == 'base64':
            logger.info(f"Encoding final image to Base64 ({media_type})...")
            temp_buffer.seek(0)
            img_bytes = temp_buffer.read()
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            logger.info("--- Image Preprocessing Finished (Base64) ---")
            return {"type": "base64", "media_type": media_type, "data": base64_image}

    except Exception as e:
        logger.error(f"Error during image preprocessing: {e}", exc_info=True)
        print(f"ERROR: Image preprocessing failed: {e}")
        return None

# Google Gemini API call with structured output
@retry_on_api_error
def call_google_llm_structured_output_text(client, model_name, system_prompt, user_prompt_parts, response_schema, logger, model_pricing_config, temperature=1.0):
    """
    Simplified version of the Google Gemini API call function for flashcard generation
    """
    if not client:
        logger.error("Google GenAI client is not available or invalid.")
        raise ValueError("Google GenAI client not initialized or invalid.")

    input_token_count = 0
    output_token_count = 0
    cost = 0.0
    token_source = "unknown"
    contents = []

    # Prepare contents list for API Call
    logger.info(f"Processing user_prompt_parts for Google Model: {model_name}")
    start_time = time.time()
    
    for i, part_data in enumerate(user_prompt_parts):
        try:
            if isinstance(part_data, str):
                contents.append(part_data)
                logger.debug(f"Added text part to contents.")
            elif isinstance(part_data, dict) and part_data.get("type") == "base64":
                base64_image = part_data['data']
                media_type_from_dict = part_data.get('media_type')
                
                save_format = 'PNG'
                mime_type_for_upload = 'image/png'

                image_buffer = BytesIO()
                image_buffer.write(base64.b64decode(base64_image))
                image_buffer.seek(0)

                display_name = f"uploaded_base64_image_{i}_{save_format.lower()}"
                logger.info(f"Uploading Base64 image as {save_format} (MIME: {mime_type_for_upload}, Display: {display_name}) to File API...")
                uploaded_file = client.files.upload(file=image_buffer, config={"mime_type": mime_type_for_upload, "display_name": display_name})
                contents.append(uploaded_file)
                logger.info(f"Image uploaded. File API URI: {uploaded_file.uri}, Name: {uploaded_file.name}")
            else:
                logger.warning(f"Unknown part type in user_prompt_parts: {type(part_data)}. Skipping.")
        except Exception as e:
            logger.error(f"Error processing part {part_data}: {e}", exc_info=True)
            raise ValueError(f"Failed to process input part: {e}") from e

    logger.info(f"Calling Google Model: {model_name} (Temp: {temperature}, JSON Output Schema: {response_schema.__name__})")
    logger.debug(f"System Prompt Provided: {bool(system_prompt)}")
    logger.debug(f"Total Parts in Contents for API Call: {len(contents)}")

    # Prepare Generation Config
    generation_config_dict = {
        "temperature": temperature,
        "response_mime_type": "application/json",
        "response_schema": response_schema,
        "system_instruction": system_prompt
    }

    try:
        generation_config = google_types.GenerateContentConfig(**generation_config_dict)
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generation_config
        )

        processing_time = time.time() - start_time

        # Check for safety blocks or empty response
        if not response.candidates:
            finish_reason = getattr(response, 'prompt_feedback', {}).get('block_reason', 'Unknown')
            log_msg = f"Google API response for {model_name} has no candidates. Finish Reason: {finish_reason}"
            logger.error(log_msg)
            raise ValueError(f"Google API response blocked or empty. Reason: {finish_reason}")

        # Token/Cost calculation from response
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
             input_token_count = response.usage_metadata.prompt_token_count
             output_token_count = response.usage_metadata.candidates_token_count

             # Add thinking tokens if available
             if response.usage_metadata.thoughts_token_count is not None:
                output_token_count += response.usage_metadata.thoughts_token_count

             token_source = "api_metadata"
             logger.info(f"Tokens from Google API metadata: Input={input_token_count}, Output={output_token_count}")
        else:
             logger.warning(f"Usage metadata missing in Google response for {model_name}")
             token_source = "metadata_missing"

        # Calculate cost (robust pricing model support)
        try:
            pricing_config = model_pricing_config.get("pricing", {}).get("google", {}).get("models", {}).get(model_name, {})
            
            if not pricing_config:
                logger.warning(f"No pricing config found for model: {model_name}")
                cost = 0.0
            else:
                # Determine input cost based on model pricing structure
                input_cost_per_m = 0
                output_cost_per_m = 0
                
                # Check for tiered pricing models first (200k threshold)
                if "input_less_than_200k_prompt" in pricing_config:
                    if input_token_count < 200_000:
                        input_cost_per_m = pricing_config.get("input_less_than_200k_prompt", 0)
                        output_cost_per_m = pricing_config.get("output_less_than_200k_prompt", 0)
                    else:
                        input_cost_per_m = pricing_config.get("input_greater_than_200k_prompt", 0)
                        output_cost_per_m = pricing_config.get("output_greater_than_200k_prompt", 0)
                    logger.debug(f"Using 200k tiered pricing for {model_name}: input={input_cost_per_m}, output={output_cost_per_m}")
                
                # Check for tiered pricing models (128k threshold)
                elif "input_less_than_128k_prompt" in pricing_config:
                    if input_token_count < 128_000:
                        input_cost_per_m = pricing_config.get("input_less_than_128k_prompt", 0)
                        output_cost_per_m = pricing_config.get("output_less_than_128k_prompt", 0)
                    else:
                        input_cost_per_m = pricing_config.get("input_greater_than_128k_prompt", 0)
                        output_cost_per_m = pricing_config.get("output_greater_than_128k_prompt", 0)
                    logger.debug(f"Using 128k tiered pricing for {model_name}: input={input_cost_per_m}, output={output_cost_per_m}")
                
                # Simple flat pricing models
                elif "input" in pricing_config and "output" in pricing_config:
                    input_cost_per_m = pricing_config.get("input", 0)
                    output_cost_per_m = pricing_config.get("output", 0)
                    logger.debug(f"Using flat pricing for {model_name}: input={input_cost_per_m}, output={output_cost_per_m}")
                
                # Calculate final cost
                cost = (input_token_count / 1_000_000 * input_cost_per_m) + (output_token_count / 1_000_000 * output_cost_per_m)
                logger.debug(f"Cost calculation: ({input_token_count}/1M * {input_cost_per_m}) + ({output_token_count}/1M * {output_cost_per_m}) = ${cost:.6f}")
        
        except Exception as e:
            logger.warning(f"Error calculating cost for {model_name}: {e}")
            cost = 0.0

        # Parse JSON response
        try:
            result_json_str = response.text.strip()
            parsed_data = json.loads(result_json_str)
            response_schema.model_validate(parsed_data)
            
            logger.info(f"API Call Complete - Model: {model_name}, Tokens: {input_token_count} in/{output_token_count} out, Cost: ${cost:.6f}, Time: {processing_time:.1f}s")
            
            return {
                "data": parsed_data,
                "input_tokens": input_token_count,
                "output_tokens": output_token_count,
                "cost": cost,
                "token_source": token_source,
                "processing_time": processing_time,
                "error": None
            }

        except (json.JSONDecodeError, Exception) as json_e:
            logger.error(f"Failed to parse or validate Google JSON response: {json_e}")
            raise ValueError(f"Invalid JSON/Schema response from Google API.") from json_e

    except google_exceptions.GoogleAPIError as e:
        is_retryable = should_retry_api_call(e)
        log_level = logging.WARNING if is_retryable else logging.ERROR
        error_message = f"Google API Error ({model_name}): {type(e).__name__} - Code: {getattr(e, 'code', 'N/A')} - {e}"
        logger.log(log_level, error_message)
        
        if not is_retryable:
             return {"data": None, "input_tokens": input_token_count, "output_tokens": output_token_count, 
                    "cost": cost, "token_source": token_source, "error": str(e)}
        else:
             raise

    except Exception as e:
        logger.error(f"Unexpected error calling Google API ({model_name}): {e}", exc_info=True)
        return {"data": None, "input_tokens": input_token_count, "output_tokens": output_token_count, 
               "cost": cost, "token_source": token_source, "error": str(e)}
    
    finally:
        # Delete uploaded files from Gemini Files API Server
        try:
            for file in client.files.list():
                client.files.delete(name=file.name)
        except Exception as cleanup_e:
            logger.warning(f"Failed to cleanup uploaded files: {cleanup_e}")


# Function to generate Japanese flashcards from uploaded images
def generate_japanese_flashcards(uploaded_images, selected_model="gemini-2.0-flash", prompt_template="Vocabulary", use_examples=True, base64_json_path="base64_example_images.json", custom_instructions=""):
    """
    For each uploaded image file:
      1) Check if the image is suitable for flashcard generation using Gemini.
      2) If suitable, extract text (OCR) via LLMWhisperer, then generate flashcards.
    Returns a string containing all flashcards from all suitable images, processing notes, and total stats.
    """
    
    # Setup logging and load configuration
    logger = setup_console_logger()
    try:
        model_config = load_model_config()
    except Exception as e:
        logger.error(f"Failed to load model configuration: {e}")
        raise ValueError("Model configuration could not be loaded. Ensure model_information.json exists and is valid.")
    
    # Load environment variables
    load_dotenv(override=True)
    is_local_dev = os.getenv("IS_LOCAL_DEV", "false").lower() == "true"

    # Handle Streamlit secrets vs local environment
    if not is_local_dev:
        try:
            secrets = getattr(st, "secrets", {})
            if "GOOGLE_GEMINI_API_KEY" in secrets:
                os.environ["GOOGLE_GEMINI_API_KEY"] = secrets["GOOGLE_GEMINI_API_KEY"]
            if "LLMWHISPERER_BASE_URL_V2" in secrets:
                os.environ["LLMWHISPERER_BASE_URL_V2"] = secrets["LLMWHISPERER_BASE_URL_V2"]
            if "LLMWHISPERER_API_KEY" in secrets:    
                os.environ["LLMWHISPERER_API_KEY"] = secrets["LLMWHISPERER_API_KEY"]
        except Exception as e:
            logger.warning(f"Could not access Streamlit secrets: {e}")

    # Get API keys
    gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    unstract_api_url = os.getenv("LLMWHISPERER_BASE_URL_V2")
    unstract_api_key = os.getenv("LLMWHISPERER_API_KEY")

    if not gemini_api_key:
        raise ValueError("GOOGLE_GEMINI_API_KEY not found in environment.")
    if not unstract_api_url:
        raise ValueError("LLMWHISPERER_BASE_URL_V2 not found in environment.")
    if not unstract_api_key:
        raise ValueError("LLMWHISPERER_API_KEY not found in environment.")

    # Initialize Google GenAI client
    try:
        client = genai.Client(api_key=gemini_api_key)
        model_name = selected_model
        logger.info(f"Initialized Google GenAI client with model: {model_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Google client: {e}")
        raise ValueError(f"Failed to initialize Google client: {e}")

    # Load and preprocess example images
    def load_base64_images_from_json(filepath="base64_example_images.json"):
        try:
            with open(filepath, 'r') as f:
                base64_images = json.load(f)
            return base64_images
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load example images from {filepath}: {e}")
            return {}

    def load_image_from_base64(base64_string):
        try:
            image_bytes = base64.b64decode(base64_string)
            image = PIL.Image.open(BytesIO(image_bytes))
            return image
        except Exception as e:
            logger.error(f"Error loading image from base64: {e}")
            return None

    # Prepare example images
    base64_example_image_dict = load_base64_images_from_json(base64_json_path)
    example_images_processed = {}
    
    if base64_example_image_dict and use_examples:
        logger.info("Processing example images...")
        image_requirements_config = model_config.get("image_requirements", {})
        
        for key, base64_data in base64_example_image_dict.items():
            pil_image = load_image_from_base64(base64_data)
            if pil_image:
                processed_image = preprocess_image(pil_image, ["google"], logger, image_requirements_config)
                if processed_image:
                    example_images_processed[key] = processed_image
                    logger.info(f"Preprocessed example image: {key}")

    # Initialize LLMWhisperer client
    llm_whisper_client = LLMWhispererClientV2(
        base_url=unstract_api_url, 
        api_key=unstract_api_key, 
        logging_level="ERROR"
    )
    
    # Process each uploaded image
    start_processing_time = time.time()
    combined_flashcards = ""
    image_processing_notes = []
    total_cost = 0.0
    total_tokens_input = 0
    total_tokens_output = 0

    for idx, uploaded_file in enumerate(uploaded_images, start=1):
        logger.info(f"Processing image #{idx}...")
        
        try:
            # Convert uploaded file to PIL image
            pil_image = PIL.Image.open(uploaded_file)
            logger.info(f"Image #{idx}: Loaded PIL image {pil_image.size}")
        except Exception as e:
            msg = f"Image #{idx}: Error opening file - {e}"
            image_processing_notes.append(msg)
            logger.error(msg)
            continue

        # Preprocess image for API upload
        try:
            image_requirements_config = model_config.get("image_requirements", {})
            processed_image = preprocess_image(pil_image, ["google"], logger, image_requirements_config)
            if not processed_image:
                msg = f"Image #{idx}: Failed to preprocess image"
                image_processing_notes.append(msg)
                logger.error(msg)
                continue
        except Exception as e:
            msg = f"Image #{idx}: Error preprocessing image - {e}"
            image_processing_notes.append(msg)
            logger.error(msg)
            continue

        # Step 1: Check suitability
        try:
            logger.info(f"Image #{idx}: Checking suitability...")
            user_prompt_parts_suitability = [
                processed_image,
                suitability_user_prompt
            ]
            
            suitability_result = call_google_llm_structured_output_text(
                client=client,
                model_name=model_name,
                system_prompt=suitability_system_prompt,
                user_prompt_parts=user_prompt_parts_suitability,
                response_schema=SuitabilityResponse,
                logger=logger,
                model_pricing_config=model_config,
                temperature=0.1
            )
            
            if suitability_result["error"]:
                msg = f"Image #{idx}: Error in suitability check - {suitability_result['error']}"
                image_processing_notes.append(msg)
                logger.error(msg)
                continue
                
            suitability_data = suitability_result["data"]
            total_cost += suitability_result["cost"]
            total_tokens_input += suitability_result["input_tokens"]
            total_tokens_output += suitability_result["output_tokens"]
            
            if suitability_data["is_suitable"] != "Yes":
                msg = f"Image #{idx}: NOT suitable for flashcard generation. Reason: {suitability_data['reason']}"
                image_processing_notes.append(msg)
                logger.info(msg)
                continue
            else:
                msg = f"Image #{idx}: Suitable for flashcards. Proceeding..."
                image_processing_notes.append(msg)
                logger.info(msg)
                
        except Exception as e:
            msg = f"Image #{idx}: Error during suitability assessment - {e}"
            image_processing_notes.append(msg)
            logger.error(msg)
            continue

        # Step 2: Extract text via OCR
        try:
            logger.info(f"Image #{idx}: Extracting text via OCR...")
            uploaded_file.seek(0)
            image_bytes = BytesIO(uploaded_file.read())
            result = llm_whisper_client.whisper(stream=image_bytes, wait_for_completion=True)
            extracted_text = result["extraction"]["result_text"]
            logger.info(f"Image #{idx}: Extracted {len(extracted_text)} characters via OCR")
        except Exception as e:
            msg = f"Image #{idx}: OCR extraction error - {e}"
            image_processing_notes.append(msg)
            logger.error(msg)
            continue

        # Step 3: Generate flashcards
        try:
            logger.info(f"Image #{idx}: Generating flashcards...")
            
            # Prepare user prompt parts based on template type
            user_prompt_parts_flashcards = []
            
            if prompt_template == "Vocabulary":
                # Add example images and prompts if enabled and available
                if use_examples and "flashcard_image_example_1" in example_images_processed and "flashcard_image_example_2" in example_images_processed:
                    user_prompt_parts_flashcards.extend([
                        example_images_processed["flashcard_image_example_1"],
                        flashcard_user_prompt_example_1,
                        flashcard_answer_example_1,
                        example_images_processed["flashcard_image_example_2"], 
                        flashcard_user_prompt_example_2,
                        flashcard_answer_example_2
                    ])
                
                # Add the actual image and prompt for vocabulary
                additional_instructions_text = f"\n## Additional Instructions:\n{custom_instructions}" if custom_instructions.strip() else ""
                user_prompt_parts_flashcards.extend([
                    processed_image,
                    flashcard_user_prompt_actual.format(
                        extracted_text=extracted_text,
                        additional_instructions=additional_instructions_text
                    )
                ])
                
                # Call API for vocabulary flashcards
                flashcard_result = call_google_llm_structured_output_text(
                    client=client,
                    model_name=model_name,
                    system_prompt=flashcard_system_prompt,
                    user_prompt_parts=user_prompt_parts_flashcards,
                    response_schema=FlashcardResponse,
                    logger=logger,
                    model_pricing_config=model_config,
                    temperature=1.0
                )
                
                if flashcard_result["error"]:
                    msg = f"Image #{idx}: Error generating flashcards - {flashcard_result['error']}"
                    image_processing_notes.append(msg)
                    logger.error(msg)
                    continue
                    
                flashcard_data = flashcard_result["data"]
                flashcard_response = FlashcardResponse(**flashcard_data)
                
            elif prompt_template == "Kanji":
                # Add the actual image and prompt for Kanji
                additional_instructions_text = f"\n## Additional Instructions:\n{custom_instructions}" if custom_instructions.strip() else ""
                user_prompt_parts_flashcards.extend([
                    processed_image,
                    flashcard_user_prompt_actual_kanji.format(
                        extracted_text=extracted_text,
                        additional_instructions=additional_instructions_text
                    )
                ])
                
                # Call API for Kanji flashcards
                flashcard_result = call_google_llm_structured_output_text(
                    client=client,
                    model_name=model_name,
                    system_prompt=flashcard_system_prompt_kanji,
                    user_prompt_parts=user_prompt_parts_flashcards,
                    response_schema=KanjiFlashcardResponse,
                    logger=logger,
                    model_pricing_config=model_config,
                    temperature=1.0
                )
                
                if flashcard_result["error"]:
                    msg = f"Image #{idx}: Error generating flashcards - {flashcard_result['error']}"
                    image_processing_notes.append(msg)
                    logger.error(msg)
                    continue
                    
                flashcard_data = flashcard_result["data"]
                flashcard_response = KanjiFlashcardResponse(**flashcard_data)
            
            # Update totals
            total_cost += flashcard_result["cost"]
            total_tokens_input += flashcard_result["input_tokens"]
            total_tokens_output += flashcard_result["output_tokens"]
            
            # Convert to CSV format
            csv_output = convert_flashcard_response_to_csv(flashcard_response)
            
            if csv_output.strip():
                combined_flashcards += csv_output + "\n"
                msg = f"Image #{idx}: Generated {len(flashcard_response.flashcards)} flashcards successfully"
                image_processing_notes.append(msg)
                logger.info(msg)
            else:
                msg = f"Image #{idx}: No flashcards generated"
                image_processing_notes.append(msg)
                logger.warning(msg)
                
        except Exception as e:
            msg = f"Image #{idx}: Error generating flashcards - {e}"
            image_processing_notes.append(msg)
            logger.error(msg)
            continue

    # Log final statistics
    total_processing_time = time.time() - start_processing_time
    logger.info(f"Processing complete - Total cost: ${total_cost:.6f}, Total tokens: {total_tokens_input} in/{total_tokens_output} out, Processing time: {total_processing_time:.1f}s")
    
    # Prepare total statistics
    total_stats = {
        'cost': total_cost,
        'tokens_input': total_tokens_input,
        'tokens_output': total_tokens_output,
        'processing_time': total_processing_time
    }
    
    return combined_flashcards.strip(), image_processing_notes, total_stats

# Function to handle the Streamlit app layout and user interaction
# No parameters
# Returns: None (runs the Streamlit UI and displays elements)
def main():
    # Setting the page configuration for Streamlit
    st.set_page_config(
        page_title="AI Japanese Flashcard Generator",
        layout="centered"
    )

    # Displaying the title for the app
    st.title("AI Japanese Flashcard Generator")

     # Displaying a banner or logo image with border
    try:
        # Load the image
        img = PIL.Image.open("Flashcard_App_Image_2.jpeg")
        
        # Add a light black border (3px width)
        bordered_img = PIL.ImageOps.expand(img, border=5, fill='#333333')
        
        # Display the image with border
        st.image(bordered_img, use_container_width=True)
    except Exception as e:
        # Fallback to display without border if there's an error
        st.image("Flashcard_App_Image_2.jpeg", use_container_width=True)

    # Displaying a short description of the app
    st.markdown("""
    ### AI Japanese Flashcard Generator

    #### Overview
    This app automates the creation of Japanese language Anki flashcards from textbook images using advanced AI technology. It combines OCR (Optical Character Recognition) with Google's Gemini language models to extract, verify, and format vocabulary or Kanji into ready-to-import flashcards.

    #### Key Features
    - **Dual Flashcard Modes**: Generate vocabulary flashcards or dedicated Kanji learning cards
    - **Multiple Gemini Models**: Choose from various [Google Gemini](https://ai.google.dev/gemini-api/docs) models (Flash, Pro, etc.) based on your needs
    - **Custom Instructions**: Add your own specific instructions to guide the AI in generating flashcards according to your requirements
    - **Intelligent Text Extraction**: Uses [LLMWhisperer OCR API](https://docs.unstract.com/llmwhisperer/) to extract text from textbook images
    - **Cross-Reference Validation**: Compares extracted text with original images for maximum accuracy
    - **Smart Highlighting Detection**: Automatically focuses on highlighted, emphasized, or colored text in source materials
    - **Structured Output**: Generates properly formatted CSV data with Pydantic schema validation
    - **Example Image Enhancement**: Optional example images improve processing accuracy (Vocabulary mode)
    - **Real-time Statistics**: Track processing costs, token usage, and generation time

    #### Supported Flashcard Types

    **Vocabulary Flashcards:**
    - **Kanji**: Word in Kanji (or Hiragana/Katakana if no Kanji exists)
    - **Furigana**: Phonetic reading in Hiragana
    - **English Translation & Notes**: Translation with contextual usage information

    **Kanji Flashcards:**
    - **Kanji**: Individual Kanji character(s)
    - **Readings**: On-yomi and Kun-yomi readings separated by " | "
    - **English Translation & Notes**: Core meanings and usage information
    - **Example Words & Sentences**: Real usage examples in context

    #### Workflow
    1. **Configuration**: Select your preferred Gemini model and flashcard type (Vocabulary or Kanji)
    2. **Custom Instructions**: Optionally add specific instructions to guide the AI's processing (e.g., "Focus on business vocabulary" or "Include more context")
    3. **Image Upload**: Upload Japanese textbook page images (JPG, JPEG, PNG)
    4. **Suitability Check**: AI assesses if images contain suitable Japanese content
    5. **Text Extraction**: LLMWhisperer OCR extracts text from images
    6. **AI Processing**: Gemini models cross-reference OCR text with original images, following your custom instructions
    7. **Flashcard Generation**: Creates structured flashcard data using specialized prompts
    8. **Export**: Download results in Anki-compatible CSV format

    #### Example Output

    **Vocabulary Format:**
    ```
    "迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
    "先輩","せんぱい","senior (student, colleague, etc.)"
    ```

    **Kanji Format:**
    ```
    "学","ガク | まな-ぶ","study, learning","学校 (がっこう) - school, 学ぶ (まなぶ) - to study"
    "生","セイ | い-きる","life, birth","学生 (がくせい) - student, 生きる (いきる) - to live"
    ```

    #### Advanced Features
    - **Cost Tracking**: Real-time monitoring of API usage costs across different Gemini models
    - **Token Analytics**: Input/output token counting for optimization
    - **Processing Statistics**: Performance metrics including generation time
    - **Error Handling**: Robust retry logic for API failures and rate limiting
    - **Image Preprocessing**: Automatic image optimization for different model requirements
    - **Customizable Processing**: Add your own instructions to tailor flashcard generation to specific needs

    #### Use Cases
    - Creating comprehensive JLPT study materials
    - Building personal vocabulary decks from textbooks
    - Generating Kanji learning flashcards with readings and examples
    - Supplementing classroom learning with digital flashcards
    - Archiving vocabulary from various Japanese learning resources
    - Batch processing multiple textbook pages efficiently
    - Customizing flashcard focus for specific topics or learning goals
    """)

    st.divider()

    # Configuration Section
    st.subheader("Configuration")
    
    # Load model configuration for dropdown options
    try:
        model_config = load_model_config()
        google_models = list(model_config.get("pricing", {}).get("google", {}).get("models", {}).keys())
    except:
        google_models = ["gemini-2.0-flash"]  # Fallback
    
    # Model selection dropdown
    selected_model = st.selectbox(
        "Select Gemini Model",
        options=google_models,
        index=google_models.index("gemini-2.0-flash") if "gemini-2.0-flash" in google_models else 0,
        help="Choose which Gemini model to use for flashcard generation"
    )
    
    # Prompt template selection
    prompt_template = st.selectbox(
        "Select Prompt Template",
        options=["Vocabulary", "Kanji"],
        index=0,
        help="Choose the type of flashcards to generate"
    )
    
    # Use example images toggle (only for Vocabulary)
    use_examples = False
    if prompt_template == "Vocabulary":
        use_examples = st.radio(
            "Use Example Images",
            options=[True, False],
            format_func=lambda x: "Yes (improved accuracy)" if x else "No (faster processing)",
            index=0,
            help="Include example images in the prompt for better accuracy (Vocabulary mode only). Please note that if you have supplied your own custom instructions, using example images may result in unexpected behavior or a decrease in accuracy."
        )

    # Custom instructions toggle and input
    st.divider()
    use_custom_instructions = st.radio(
        "Add Custom Instructions",
        options=[False, True],
        format_func=lambda x: "Yes" if x else "No",
        index=0,
        help="Add your own custom instructions to guide the AI in generating flashcards. Please note that these instructions can only influence the content and focus of the generated flashcards. They cannot change the output format."
    )
    
    custom_instructions = ""
    if use_custom_instructions:
        custom_instructions = st.text_area(
            "Custom Instructions",
            placeholder="Enter additional instructions for the AI. For example: 'Focus on business vocabulary' or 'Include more context from surrounding sentences'. These instructions cannot change the output format, but can influence the content and focus of the generated flashcards.",
            help="These instructions will be added to the AI prompt to customize flashcard generation.",
            height=130
        )

    # Providing a file uploader for users to add images
    uploaded_images = st.file_uploader(
        "Upload image(s) of textbook pages",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    # Button to initiate flashcard generation
    if st.button("Generate Flashcards"):
        if not uploaded_images:
            st.warning("Please upload at least one image.")
        else:
            with st.spinner("Processing..."):
                try:
                    # Generate the flashcards by calling the function
                    flashcards_str, processing_notes, total_stats = generate_japanese_flashcards(
                        uploaded_images=uploaded_images,
                        selected_model=selected_model,
                        prompt_template=prompt_template,
                        use_examples=use_examples,
                        base64_json_path="base64_example_images.json",
                        custom_instructions=custom_instructions if use_custom_instructions else ""
                    )

                    # Display the processing status for each image
                    for note in processing_notes:
                        st.info(note)

                    # Display total statistics
                    st.success(f"Processing complete! Total cost: ${total_stats['cost']:.6f}, Total tokens: {total_stats['tokens_input']:,} in/{total_stats['tokens_output']:,} out, Processing time: {total_stats['processing_time']:.1f}s")

                    # If we have at least some flashcards, show a download button
                    if flashcards_str.strip():
                        st.download_button(
                            label="Download Flashcards",
                            data=flashcards_str,
                            file_name="generated_flashcards.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("No flashcards were generated from the uploaded images.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    # Log the full error for debugging
                    logger = setup_console_logger()
                    logger.error(f"Streamlit app error: {e}", exc_info=True)


# This condition ensures the script is run directly through Streamlit
if __name__ == "__main__":
    main()