import base64
import logging
import os
from .connectors import get_ollama_client
from .prompts import IMAGE_ANALYSIS_PROMPTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def encode_image_to_base64(image_path):
    """Encodes an image file to a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except IOError as e:
        logging.error(f"Error opening or reading image file {image_path}: {e}")
        return None

def analyze_image_with_vlm(image_path, document_context=None, image_type_hint='GENERIC'):
    """
    Analyzes an image using the Qwen VL model with a dynamically selected prompt.

    Args:
        image_path (str): The path to the image file.
        document_context (str, optional): Textual context from the document.
        image_type_hint (str, optional): A hint for which specialized prompt to use.
                                        Defaults to 'GENERIC'.

    Returns:
        str: The analysis result from the VLM.
    """
    client = get_ollama_client()
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return "Error: Image could not be encoded."

    # Dynamically select the prompt from the imported dictionary
    prompt_text = IMAGE_ANALYSIS_PROMPTS.get(image_type_hint.upper(), IMAGE_ANALYSIS_PROMPTS["GENERIC"])

    # Include document context if available
    if document_context:
        prompt_text += f"\n\nADDITIONAL CONTEXT FROM THE DOCUMENT:\n{document_context}"

    logging.info(f"Analyzing image {os.path.basename(image_path)} using '{image_type_hint}' prompt.")

    try:
        response = client.generate(
            model="qwen2.5-vl:latest",
            prompt=prompt_text,
            images=[base64_image],
            options={
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 2048
            }
        )
        
        return response.get("response", "No response generated")
    except Exception as e:
        logging.error(f"An error occurred during VLM invocation for image {image_path}: {e}")
        return f"Error during analysis: {e}"

if __name__ == '__main__':
    pass
