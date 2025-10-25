import os
import pathlib
import re
from PIL import Image
import base64
import requests
import json
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

def setup_roboflow():
    """Initialize Roboflow client configuration from environment variables."""
    api_url = os.getenv("ROBOFLOW_API_URL", "https://serverless.roboflow.com")
    api_key = os.getenv("ROBOFLOW_API_KEY")
    model_id = os.getenv("ROBOFLOW_MODEL_ID")
    
    if not api_key:
        raise ValueError("Please set ROBOFLOW_API_KEY in the .env file")
    if not model_id:
        raise ValueError("Please set ROBOFLOW_MODEL_ID in the .env file")
    
    return {
        'api_url': api_url,
        'api_key': api_key,
        'model_id': model_id
    }

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

def process_image(client_config, image_path):
    """Extract KWh readings from an image using Roboflow."""
    try:
        print(f"\nProcessing image: {image_path}")
        
        # Prepare the API request
        url = f"{client_config['api_url']}/{client_config['model_id']}"
        
        # Read and encode the image
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        # Prepare headers
        headers = {
            'Authorization': f"Bearer {client_config['api_key']}"
        }
        
        # Prepare files for multipart upload
        files = {
            'file': ('image.jpg', image_data, 'image/jpeg')
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Raw Roboflow response: {result}")  # Debug print
            
            # Extract predictions from Roboflow response
            predictions = result.get('predictions', [])
            if not predictions:
                print("No predictions found in Roboflow response")
                return "No KWh readings found"
            
            # Extract text from predictions (assuming OCR results)
            extracted_text = ""
            for prediction in predictions:
                if 'text' in prediction:
                    extracted_text += prediction['text'] + " "
                elif 'class' in prediction:
                    extracted_text += prediction['class'] + " "
            
            print(f"Extracted text from Roboflow: {extracted_text}")  # Debug print
            
            # Extract KWh values from the response
            kwh_values = extract_kwh_values(extracted_text)
            print(f"All found KWh values: {kwh_values}")  # Debug print
            
            if not kwh_values:
                print("No KWh values found in the text")  # Debug print
                return "No KWh readings found"
            
            # Return the first valid reading found
            return f"{kwh_values[0]:.0f} KWh"
        else:
            print(f"Roboflow API error: {response.status_code} - {response.text}")
            return "No KWh readings found"
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return "No KWh readings found"

def main():
    """Main function for testing."""
    try:
        # Initialize Roboflow
        client_config = setup_roboflow()
        print("Roboflow client initialized successfully")
        
        # Process all images in input directory
        input_dir = 'input'
        if not os.path.exists(input_dir):
            os.makedirs(input_dir)
            
        while True:
            for filename in os.listdir(input_dir):
                if filename.endswith('.jpg'):
                    image_path = os.path.join(input_dir, filename)
                    print(f"\nProcessing {filename}...")
                    reading = process_image(client_config, image_path)
                    print(f"Reading: {reading}")
            
            time.sleep(5)  # Wait 5 seconds before checking again
            
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
