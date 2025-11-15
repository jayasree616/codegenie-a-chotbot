import google.genai as genai
import os
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# --- Client Initialization ---
def get_gemini_response(prompt: str):
    """
    Calls the Gemini API with the given prompt and returns the response text.
    If API key is missing or invalid, returns an error message.
    """
    try:
        if not API_KEY:
            return "❌ Error: GEMINI_API_KEY not found. Please set it in your environment."

        # Initialize Gemini client
        client = genai.Client(api_key=API_KEY)

        # Call the model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        error_text = f"⚠️ Error: {str(e)}"
        if "API_KEY_INVALID" in str(e):
            error_text += "\nReminder: Use a valid API key from Google AI Studio."
        elif "PERMISSION_DENIED" in str(e):
            error_text += "\nYour API key may not have access to Gemini API."
        return error_text
