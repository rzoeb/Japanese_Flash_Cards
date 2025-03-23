# Building a Streamlit UI for code in 'Flashcard_Generation_LLM.ipynb'
# Importing the required libraries
import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from unstract.llmwhisperer import LLMWhispererClientV2
import os
from io import BytesIO
from dotenv import load_dotenv
import base64

# Importing all variables from LLM_Prompts.py
from LLM_Prompts import *

# Function to generate Japanese flashcards from uploaded images
# uploaded_images: A list of file-like objects (from Streamlit's uploader)
# base64_json_path: The path to a JSON file containing base64-encoded example images
# Returns: A string containing all generated flashcards (or reasons if not suitable)
def generate_japanese_flashcards(
    uploaded_images,
    base64_json_path="base64_example_images.json"
    ):
    """
    For each uploaded image file:
      1) Check if the image is suitable for flashcard generation using Gemini.
      2) If suitable, extract text (OCR) via LLMWhisperer, then generate flashcards.
    Returns a string containing all flashcards from all suitable images.

    This function reads the prompt variables (suitability_system_prompt, etc.)
    from the global namespace, as imported by `from LLM_Prompts import *`.
    """

    # -----------------------------
    # Load environment variables
    # -----------------------------
    load_dotenv()
    gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    unstract_api_url = os.getenv("LLMWHISPERER_BASE_URL_V2")
    unstract_api_key = os.getenv("LLMWHISPERER_API_KEY")

    if not gemini_api_key:
        raise ValueError("GOOGLE_GEMINI_API_KEY not found in environment.")
    if not unstract_api_url:
        raise ValueError("LLMWHISPERER_BASE_URL_V2 not found in environment.")
    if not unstract_api_key:
        raise ValueError("LLMWHISPERER_API_KEY not found in environment.")

    # -----------------------------
    # Configure the Gemini model
    # -----------------------------
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    # model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

    # -----------------------------
    # Utility functions
    # -----------------------------
    # Function to load base64 images from a JSON file
    # filepath: Path to the JSON file containing base64 image strings
    # Returns: Dictionary with image names as keys and PIL Image objects as values. Empty dictionary returned on error.
    def load_base64_images_from_json(filepath="base64_example_images.json"):
        try:
            with open(filepath, 'r') as f:
                base64_images = json.load(f)
            return base64_images
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {filepath}")
            return {}

    # Function to load a base64 image string into a PIL Image object
    # base64_string: Base64 encoded image string
    # Returns: PIL Image object or None on error
    def load_image_from_base64(base64_string):
        try:
            image_bytes = base64.b64decode(base64_string)
            image = PIL.Image.open(BytesIO(image_bytes))
            return image
        except Exception as e:
            print(f"Error loading image from base64: {e}")
            return None
    
    # -----------------------------
    # Prepare example images
    # -----------------------------
    base64_example_image_dict = load_base64_images_from_json()
    if base64_example_image_dict:
        image_example_1 = load_image_from_base64(base64_example_image_dict["flashcard_image_example_1"])
        image_example_2 = load_image_from_base64(base64_example_image_dict["flashcard_image_example_2"])

    # -----------------------------
    # LLMWhisperer client
    # -----------------------------
    client = LLMWhispererClientV2(base_url=unstract_api_url, 
                                  api_key=unstract_api_key, 
                                  logging_level="ERROR")
    
    # -----------------------------
    # Process each uploaded image
    # -----------------------------
    # Initialize a string to store flashcards for all suitable images
    combined_flashcards = ""

    # Initialize a list to store status notes for each image
    image_processing_notes = []

     # Iterate over each uploaded image
    for idx, uploaded_file in enumerate(uploaded_images, start=1):
        # Convert uploaded file to a PIL image
        try:
            pil_image = PIL.Image.open(uploaded_file)
        except Exception as e:
            msg = f"Image #{idx}: Error opening file - {e}"
            image_processing_notes.append(msg)
            continue  # Move on to the next image

        # Prepare the content for suitability check
        content_suitability = [
            suitability_system_prompt,
            pil_image,
            suitability_user_prompt,
        ]

        # Check if the image is suitable for flashcard generation
        try:
            response_suitability = model.generate_content(content_suitability)
            response_suitability.resolve()  # Raises an exception on error
            # Extract JSON-like text from the model response
            json_string = (
                response_suitability.text
                    .replace("```json", "")
                    .replace("```", "")
            )
            suitability_data = json.loads(json_string)
            is_suitable = suitability_data.get("is_suitable")
            reason = suitability_data.get("reason")
        except Exception as e:
            msg = f"Image #{idx}: Error generating suitability assessment - {e}"
            image_processing_notes.append(msg)
            continue

        # If not suitable, record a note and skip further processing
        if is_suitable != "Yes":
            msg = f"Image #{idx}: NOT suitable for flashcard generation. Reason: {reason}"
            image_processing_notes.append(msg)
            continue
        else:
            image_processing_notes.append(f"Image #{idx}: Suitable for flashcards. Proceeding...")

        # If suitable, extract the text from the image via LLMWhisperer (OCR)
        try:
            uploaded_file.seek(0)  # Reset file pointer
            image_bytes = BytesIO(uploaded_file.read())
            result = client.whisper(stream=image_bytes, wait_for_completion=True)
            image_actual_extracted_text = result["extraction"]["result_text"]
        except Exception as e:
            msg = f"Image #{idx}: OCR extraction error - {e}"
            image_processing_notes.append(msg)
            continue

        # Prepare the content for flashcard generation
        content_flashcards = [flashcard_system_prompt]

        # If example images are available, include them in the prompt
        if image_example_1 and image_example_2:
            content_flashcards += [
                image_example_1,
                flashcard_user_prompt_example_1,
                flashcard_answer_example_1,
                image_example_2,
                flashcard_user_prompt_example_2,
                flashcard_answer_example_2,
            ]

        # Add the user prompt for the actual image's extracted text
        content_flashcards += [
            pil_image,
            flashcard_user_prompt_actual.format(extracted_text=image_actual_extracted_text),
        ]

        # Generate the flashcards using Gemini
        try:
            response_flashcards = model.generate_content(content_flashcards)
            response_flashcards.resolve()  # Raises an exception on error
            flashcards_text = (
                response_flashcards.text
                    .replace("```html", "")
                    .replace("```csv", "")
                    .replace("```", "")
            )
        except Exception as e:
            msg = f"Image #{idx}: Error generating flashcards - {e}"
            image_processing_notes.append(msg)
            continue

        # If we made it here, flashcards were generated successfully
        # combined_flashcards += f"\n---\nFlashcards for Image #{idx}:\n{flashcards_text}\n---\n"
        combined_flashcards += flashcards_text
        image_processing_notes.append(f"Image #{idx}: Flashcards generated successfully.")

    # Return both the flashcards and the notes
    return combined_flashcards, image_processing_notes

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
    ### Japanese Language Flashcard Generation

    #### Overview
    This App automates the creation of Japanese Language Anki flashcards from textbook images. It combines OCR technology with large language model processing to extract, verify, and format vocabulary into ready-to-import flashcards.

    #### Features
    - Extract Japanese text from textbook images using OCR API
    - Cross-reference extracted text with original images for accuracy
    - Generate structured CSV flashcards with proper formatting
    - Support for contextual vocabulary notes and usage examples

    #### Workflow
    1. **Image Upload**: Upload Japanese textbook page images  
    2. **Text Extraction**: Use OCR API to extract text from the images (Currently the [LLMWhisperer API](https://docs.unstract.com/llmwhisperer/) is used)  
    3. **LLM Processing**: Send both the extracted text and original image to an LLM (Currently the [Gemini API](https://ai.google.dev/gemini-api/docs?_gl=1*12oxa0f*_up*MQ..*_ga*MzA5MjA0NTQ0LjE3NDI2OTMzNzE.*_ga_P1DBVKWT6V*MTc0MjY5MzM3MC4xLjAuMTc0MjY5MzM3MC4wLjAuNDgyMDU2NTA5) is used)  
    4. **Flashcard Generation**: Generate structured CSV data using specialized prompts  
    5. **Export**: Save the resulting flashcards in Anki-compatible CSV format  

    #### Flashcard Format
    The generated flashcards follow a specific CSV structure:
    - **Kanji column**: Contains the word in Kanji (or Hiragana/Katakana if no Kanji exists)  
    - **Furigana column**: Contains the phonetic reading of the word in Hiragana  
    - **English_Translation_and_Notes column**: Contains both the English translation and any usage or contextual notes  

    Example output:
    ```
    "迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
    "先輩","せんぱい","senior (student, colleague, etc.)"
    ```

    #### Benefits
    - **Accuracy**: Cross-references OCR text with the original image to fix errors  
    - **Context-Aware**: Preserves usage examples and contextual information  
    - **Time-Saving**: Automates the tedious process of manual flashcard creation  
    - **Customizable**: Prompts can be adjusted for different textbook formats  

    #### Applications
    - Creating comprehensive JLPT study materials  
    - Building personal vocabulary decks from textbooks  
    - Supplementing classroom learning with digital flashcards  
    - Archiving vocabulary from various Japanese learning resources
    """)

    st.divider()

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
                    flashcards_str, processing_notes = generate_japanese_flashcards(
                        uploaded_images=uploaded_images,
                        base64_json_path="base64_example_images.json"  # Adjust if needed
                    )

                    # Display the processing status for each image
                    for note in processing_notes:
                        st.info(note)

                    # If we have at least some flashcards, show a download button
                    if flashcards_str.strip():
                        st.download_button(
                            label="Download Flashcards",
                            data=flashcards_str,
                            file_name="generated_flashcards.txt",
                            mime="text/plain"
                        )
                        st.success("Flashcards generated successfully!")
                    else:
                        st.warning("No flashcards were generated from the uploaded images.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                # Example of writing to disk with UTF-8 (if needed):
                # with open("generated_flashcards.txt", "w", encoding="utf-8") as f:
                #     f.write(flashcards_str)


# This condition ensures the script is run directly through Streamlit
if __name__ == "__main__":
    main()