import os
import pathlib
import re
from PIL import Image
import base64
import google.generativeai as genai
from google.generativeai import types
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Initializes and returns the Gemini Vision API client using the API key from the environment.
def setup_gemini():
    """Initialize Gemini API with the API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY in the .env file")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')  # Using the suggested model

def extract_kwh_values(text):
    """Extract KWh values from text using regex patterns."""
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:KWh|kwh|kWh|kwH|KWH)\b',  # Matches: 1558kwh, 1558 KWh
        r'(\d{4,})',  # Matches any 4+ digit number (likely a meter reading)
        r'\b(\d+(?:\.\d+)?)\s*(?:units?)\b',  # Matches: 1558 units
        r'(?:reading|consumption|value|number)[:=]?\s*(\d+(?:\.\d+)?)',  # Matches: reading: 1558
    ]
    
    found_values = []
    print(f"\nSearching text: {text}")  # Debug print
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                value = float(match.group(1))
                print(f"Found match with pattern '{pattern}': {value}")  # Debug print
                found_values.append(value)
            except ValueError as e:
                print(f"Error converting match to float: {e}")
    
    return found_values

def process_image(model, image_path):
    """Extract KWh readings from an image using Gemini Vision."""
    try:
        print(f"\nProcessing image: {image_path}")
        
        # Open and convert image
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        prompt = (
            "This is an electricity meter reading image. "
            "Please identify and extract any numbers that represent electricity consumption. "
            "Look for patterns like 'KWh', 'units', or similar values. "
            "Return ONLY the number you see, with 'KWh' unit if visible. "
            "If no valid reading is found, return 'No KWh readings found'."
        )
        
        response = model.generate_content([prompt, img])
        extracted_text = response.text
        print(f"Raw extracted text from Gemini: {extracted_text}")  # Debug print
        
        # Extract KWh values from the response
        kwh_values = extract_kwh_values(extracted_text)
        print(f"All found KWh values: {kwh_values}")  # Debug print
        
        if not kwh_values:
            print("No KWh values found in the text")  # Debug print
            return "No KWh readings found"
        
        # Return the first valid reading found
        return f"{kwh_values[0]:.0f} KWh"
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return "No KWh readings found"

def main():
    """Main function for testing."""
    try:
        # Initialize Gemini
        model = setup_gemini()
        print("Model initialized successfully")
        
        # Process all images in input directory
        input_dir = 'input'
        if not os.path.exists(input_dir):
            os.makedirs(input_dir)
            
        while True:
            for filename in os.listdir(input_dir):
                if filename.endswith('.jpg'):
                    image_path = os.path.join(input_dir, filename)
                    print(f"\nProcessing {filename}...")
                    reading = process_image(model, image_path)
                    print(f"Reading: {reading}")
            
            time.sleep(5)  # Wait 5 seconds before checking again
            
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
