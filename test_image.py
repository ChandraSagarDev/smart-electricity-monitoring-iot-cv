from extract_text import setup_gemini, process_image

def test_single_image():
    # Initialize Gemini
    model = setup_gemini()
    print("Model initialized")
    
    # Process both enhanced and original image
    image_path = "input/enhanced_20250330_174043.jpg"
    print(f"\nTesting enhanced image: {image_path}")
    result = process_image(model, image_path)
    print(f"Enhanced image result: {result}")
    
    image_path = "input/original_20250330_174043.jpg"
    print(f"\nTesting original image: {image_path}")
    result = process_image(model, image_path)
    print(f"Original image result: {result}")

# Entry point for running the image processing and reading extraction tests.
if __name__ == "__main__":
    test_single_image()
