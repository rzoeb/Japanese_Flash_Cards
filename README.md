# AI Japanese Flashcard Generator

An advanced tool that automates the creation of Japanese language Anki flashcards from textbook images using cutting-edge AI technology, including Google's Gemini language models and OCR processing.

## Overview

This application extracts Japanese vocabulary and Kanji from textbook images and generates properly formatted flashcards that can be imported into Anki or similar spaced repetition systems. It combines OCR technology with Google's Gemini language models to extract, verify, and format content into ready-to-import flashcards with advanced AI-powered processing.

## Key Features

- **Dual Flashcard Modes**: Generate vocabulary flashcards or dedicated Kanji learning cards
- **Multiple Gemini Models**: Choose from various Google Gemini models (Flash, Pro, etc.) based on your needs
- **Intelligent Text Extraction**: Uses LLMWhisperer OCR API to extract text from textbook images
- **Cross-Reference Validation**: Compares extracted text with original images for maximum accuracy
- **Smart Highlighting Detection**: Automatically focuses on highlighted, emphasized, or colored text in source materials
- **Structured Output**: Generates properly formatted CSV data with Pydantic schema validation
- **Example Image Enhancement**: Optional example images improve processing accuracy (Vocabulary mode)
- **Real-time Statistics**: Track processing costs, token usage, and generation time
- **Advanced Error Handling**: Robust retry logic for API failures and rate limiting
- **Image Preprocessing**: Automatic image optimization for different model requirements

## Supported Flashcard Types

### Vocabulary Flashcards
- **Kanji**: Word in Kanji (or Hiragana/Katakana if no Kanji exists)
- **Furigana**: Phonetic reading in Hiragana
- **English Translation & Notes**: Translation with contextual usage information

### Kanji Flashcards
- **Kanji**: Individual Kanji character(s)
- **Readings**: On-yomi and Kun-yomi readings separated by " | "
- **English Translation & Notes**: Core meanings and usage information
- **Example Words & Sentences**: Real usage examples in context

## Example Output

### Vocabulary Format:
```
"迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
"先輩","せんぱい","senior (student, colleague, etc.)"
```

### Kanji Format:
```
"学","ガク | まな-ぶ","study, learning","学校 (がっこう) - school, 学ぶ (まなぶ) - to study"
"生","セイ | い-きる","life, birth","学生 (がくせい) - student, 生きる (いきる) - to live"
```

## Repository Contents

- `app.py` - Main Streamlit application with advanced UI controls for model and prompt selection
- `LLM_Prompts.py` - All prompt templates for suitability checking, vocabulary generation, and Kanji flashcard creation
- `model_information.json` - Configuration file containing model specifications, pricing, and image requirements
- `base64_example_images.json` - Example images encoded in base64 format for enhanced processing accuracy
- `requirements.txt` - Updated Python dependencies including Google GenAI SDK and Pydantic
- Sample images: `Flashcard_App_Image_1.jpg` and `Flashcard_App_Image_2.jpeg`
- `unstract_multiple_llm_text_image.py` - Advanced image preprocessing utilities

## Setup and Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional for Web Interface)** Create a .env file in the root directory with the following variables:
   ```
   IS_LOCAL_DEV=true
   GOOGLE_GEMINI_API_KEY=your_gemini_api_key
   LLMWHISPERER_BASE_URL_V2=your_llmwhisperer_base_url
   LLMWHISPERER_API_KEY=your_llmwhisperer_api_key
   ```

   **Note**: You can either:
   - Create a `.env` file with your API keys (recommended for local development)
   - Or enter your API keys directly in the web interface when running the app
   
   You'll need to obtain:
   - A Google Gemini API key from [Google AI Studio](https://ai.google.dev/gemini-api/docs/quickstart)
   - Access to [LLMWhisperer API](https://docs.unstract.com/llmwhisperer/llm_whisperer/getting_started/llm_whisperer_registering/)

4. Ensure `model_information.json` is present in the root directory (contains model configurations and pricing information)

## Usage

There are two main ways to use the AI Japanese Flashcard Generator:

### Method 1: Using the Streamlit Web Interface (Recommended)

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open the provided URL in your browser (typically http://localhost:8501)

3. **Enter your API keys:**
   - **Google Gemini API Key**: [Get your API key here](https://ai.google.dev/gemini-api/docs/quickstart)
   - **LLMWhisperer API Key**: [Register and get your API key here](https://docs.unstract.com/llmwhisperer/llm_whisperer/getting_started/llm_whisperer_registering/)
   - **Privacy**: Your API keys are only used for the current session and are never stored

4. **Configure your settings:**
   - Select your preferred Gemini model from the dropdown
   - Choose flashcard type: "Vocabulary" or "Kanji"
   - For Vocabulary mode: Toggle example images on/off for enhanced accuracy

5. Upload one or more textbook images containing Japanese vocabulary (JPG, JPEG, PNG)

6. Click "Generate Flashcards" to process the images

7. View real-time processing statistics including costs, tokens, and generation time

8. Download the generated flashcards as a CSV file ready for Anki import

**Note**: If running locally with a `.env` file, API keys from the environment will be used as fallback if the input fields are left empty.

### Method 2: Customizing and Running the Code Locally

For advanced users who want to customize the processing logic, modify prompts, or integrate the functionality into their own applications:

1. **Open and examine `app.py`** to understand the core functions:
   - `generate_japanese_flashcards()` - Main processing function
   - `call_google_llm_structured_output_text()` - Gemini API interface
   - `preprocess_image()` - Image optimization utilities
   - `convert_flashcard_response_to_csv()` - Output formatting

2. **Customize the processing** by modifying:
   - Prompt templates in `LLM_Prompts.py`
   - Model configurations in `model_information.json`
   - Image preprocessing parameters
   - Output formatting and CSV structure

3. **Run custom processing** by calling the functions directly:
   ```python
   from app import generate_japanese_flashcards
   from PIL import Image
   
   # Load your images
   images = [uploaded_file_1, uploaded_file_2]  # Your image files
   
   # Generate flashcards with custom settings
   flashcards, notes, stats = generate_japanese_flashcards(
       uploaded_images=images,
       selected_model="gemini-2.0-flash",
       prompt_template="Vocabulary",
       use_examples=True
   )
   ```

4. **Integrate into your workflow** by importing and using the individual functions as needed

This approach allows for complete customization of the flashcard generation process while maintaining access to all the advanced features like cost tracking, error handling, and schema validation.

## Enhanced Workflow

1. **Configuration**: Select your preferred Gemini model and flashcard type (Vocabulary or Kanji)
2. **Image Upload**: Upload Japanese textbook page images (JPG, JPEG, PNG)
3. **Suitability Check**: AI assesses if images contain suitable Japanese content for flashcard generation
4. **Text Extraction**: LLMWhisperer OCR API extracts text from images with high accuracy
5. **AI Processing**: Gemini models cross-reference OCR text with original images using advanced prompts
6. **Smart Detection**: Automatically identifies highlighted, emphasized, or colored text as priority content
7. **Flashcard Generation**: Creates structured flashcard data using specialized prompts and Pydantic validation
8. **Statistics & Export**: View processing metrics and download results in Anki-compatible CSV format

## Advanced Features

- **Cost Tracking**: Real-time monitoring of API usage costs across different Gemini models
- **Token Analytics**: Input/output token counting for optimization and usage tracking
- **Processing Statistics**: Performance metrics including generation time and success rates
- **Error Handling**: Robust retry logic with exponential backoff for API failures and rate limiting
- **Image Preprocessing**: Automatic image optimization based on model-specific requirements
- **Schema Validation**: Pydantic-based output validation ensures consistent, high-quality results

## Dependencies

The application requires the following Python packages:
- `streamlit` - For the advanced web application interface with model selection
- `google-genai>=0.2.0` - Latest Google GenAI SDK for Gemini API access with structured output
- `Pillow` - For comprehensive image processing and optimization
- `python-dotenv` - For secure environment variable management
- `unstract-llmwhisperer` - For high-accuracy OCR capabilities via the LLMWhisperer API
- `pydantic` - For robust data validation and structured output schemas
- `tenacity` - For intelligent retry logic and error handling
- `typing` - For enhanced type hints and validation

All dependencies with specific version requirements are listed in the requirements.txt file.

## Use Cases

- **JLPT Preparation**: Create comprehensive study materials for Japanese Language Proficiency Tests
- **Textbook Digitization**: Convert physical textbook vocabulary into digital flashcard format
- **Kanji Learning**: Generate dedicated Kanji flashcards with readings, meanings, and usage examples
- **Classroom Integration**: Supplement traditional learning with modern spaced repetition techniques
- **Personal Study**: Build customized vocabulary decks from various Japanese learning resources
- **Batch Processing**: Efficiently process multiple textbook pages and chapters
- **Academic Research**: Archive and analyze vocabulary patterns from educational materials

## System Requirements

- **Python**: 3.8+ (3.10+ recommended for optimal performance)
- **Google Gemini API**: Access to Google's Gemini models (Flash, Pro, etc.)
- **LLMWhisperer API**: Access for high-accuracy OCR processing
- **Memory**: Minimum 4GB RAM (8GB recommended for processing multiple large images)
- **Storage**: At least 1GB free space for image processing and model caching
- **Internet**: Stable connection required for API calls

## Configuration Files

- **model_information.json**: Contains model specifications, pricing information, and image requirements
- **.env**: Secure storage for API keys and configuration variables (excluded from version control)
- **base64_example_images.json**: Pre-encoded example images for enhanced processing accuracy

## Performance & Costs

The application provides real-time tracking of:
- **API Costs**: Per-request pricing across different Gemini models
- **Token Usage**: Input and output token consumption monitoring
- **Processing Time**: End-to-end generation time measurement
- **Success Rates**: Image suitability and processing success metrics

## Security & Privacy

- API keys are stored securely in environment variables
- No user data is permanently stored on external servers
- All image processing respects original file privacy
- Configurable local development mode for enhanced security

## License

See the LICENSE file for details.

## Note

**API Key Management**: You can provide API keys in two ways:
- **Direct Input**: Enter API keys directly in the web interface (recommended for most users)
- **Environment File**: Create a `.env` file with your API keys (recommended for local development)

The `.env` file containing API keys and configuration secrets is excluded from version control for security reasons. The application includes comprehensive error handling and will provide clear guidance if configuration issues are detected.

**Privacy**: API keys entered in the web interface are only used for the current session and are never stored or transmitted to third parties.

## Recent Updates

This version includes major enhancements:
- **Secure API Key Input**: Enter API keys directly in the web interface with session-only storage
- Migration to Google GenAI SDK with structured output capabilities
- Dual-mode flashcard generation (Vocabulary and Kanji)
- Advanced model selection and configuration options
- Real-time cost and performance tracking
- Enhanced error handling and retry logic
- Improved image preprocessing and optimization
- Pydantic-based schema validation for reliable output