# Japanese Flashcard Generator

A tool that automates the creation of Japanese language Anki flashcards from textbook images by leveraging OCR technology and Large Language Models.

## Overview

This application extracts Japanese vocabulary from textbook images and generates properly formatted flashcards that can be imported into Anki or similar spaced repetition systems. It combines OCR technology with large language model processing to extract, verify, and format vocabulary into ready-to-import flashcards.

## Features

- Extract Japanese text from textbook images using OCR technology
- Cross-reference extracted text with original images for accuracy
- Generate structured CSV flashcards with proper formatting
- Support for contextual vocabulary notes and usage examples
- Simple UI for uploading images and downloading flashcards

## Flashcard Format

The generated flashcards follow a specific CSV structure:
- **Kanji column**: Contains the word in Kanji (or Hiragana/Katakana if no Kanji exists)
- **Furigana column**: Contains the phonetic reading of the word in Hiragana
- **English_Translation_and_Notes column**: Contains both the English translation and any usage or contextual notes

Example output:
```
"迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
"先輩","せんぱい","senior (student, colleague, etc.)"
```

## Repository Contents

- `app.py` - Streamlit UI for the flashcard generator
- `Flashcard_Generation_LLM.ipynb` - Jupyter notebook for experimentation (contains self-contained instructions)
- `LLM_Prompts.py` - Prompts used for the LLM processing
- `base64_example_images.json` - Example images encoded in base64 format
- `requirements.txt` - List of Python dependencies
- Sample images: `Flashcard_App_Image_1.jpg` and `Flashcard_App_Image_2.jpeg`

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

3. Create a .env file in the root directory with the following variables:
   ```
   IS_LOCAL_DEV = true
   GOOGLE_GEMINI_API_KEY=your_gemini_api_key
   LLMWHISPERER_BASE_URL_V2=your_llmwhisperer_base_url
   LLMWHISPERER_API_KEY=your_llmwhisperer_api_key
   ```

   You'll need to obtain:
   - A Google Gemini API key from [Google AI Studio](https://ai.google.dev/)
   - Access to [LLMWhisperer API](https://docs.unstract.com/llmwhisperer/) for OCR capabilities

## Usage

### Using the Streamlit UI

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open the provided URL in your browser (typically http://localhost:8501)

3. Upload one or more textbook images containing Japanese vocabulary

4. Click "Generate Flashcards" to process the images

5. Download the generated flashcards as a text file

### Using the Jupyter Notebook

The Flashcard_Generation_LLM.ipynb notebook contains self-contained instructions and can be used for experimentation and customization. It's a great way to understand the workflow and make adjustments to the prompts or processing logic.

## Workflow

1. **Image Upload**: Upload Japanese textbook page images
2. **Suitability Check**: Verify if the images contain appropriate Japanese text
3. **Text Extraction**: Use OCR API to extract text from the images
4. **LLM Processing**: Process both the extracted text and original image with an LLM
5. **Flashcard Generation**: Generate structured data using specialized prompts
6. **Download**: Save the resulting flashcards in Anki-compatible format

## Dependencies

The application requires the following Python packages:
- `streamlit` - For the web application interface
- `google-generativeai` - To interact with Google's Gemini API
- `Pillow` - For image processing
- `python-dotenv` - For loading environment variables
- `unstract-llmwhisperer` - For OCR capabilities via the LLMWhisperer API

All dependencies are listed in the requirements.txt file.

## Applications

- Creating comprehensive JLPT study materials
- Building personal vocabulary decks from textbooks
- Supplementing classroom learning with digital flashcards
- Archiving vocabulary from various Japanese learning resources

## Requirements

- Python 3.8+
- Google Gemini API access
- LLMWhisperer API access
- Required Python packages (listed in requirements.txt)

## License

See the LICENSE file for details.

## Note

The .env file containing API keys and secrets is excluded from version control for security reasons. You'll need to create this file with your own API keys as described in the setup instructions.