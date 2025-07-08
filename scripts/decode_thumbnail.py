import json
import base64
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("decode_thumbnail")

def decode_thumbnail(json_file, output_file="thumbnail.jpg"):
    """Decode base64 thumbnail from JSON response."""
    
    try:
        # Read JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract base64 thumbnail
        thumbnail_b64 = data.get('thumbnail_b64')
        if not thumbnail_b64:
            logger.error("No thumbnail_b64 found in JSON response")
            return False
        
        # Decode base64 to binary
        thumbnail_data = base64.b64decode(thumbnail_b64)
        
        # Save as image file
        with open(output_file, 'wb') as f:
            f.write(thumbnail_data)
        
        logger.info("Thumbnail saved as: {}".format(output_file))
        logger.info("Size: {} bytes".format(len(thumbnail_data)))
        return True
        
    except Exception as e:
        logger.error("Error decoding thumbnail: {}".format(e))
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        logger.info("Usage: python decode_thumbnail.py <json_file> [output_file]")
        logger.info("Example: python decode_thumbnail.py response.json thumbnail.jpg")
        return
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "thumbnail.jpg"
    
    decode_thumbnail(json_file, output_file)

if __name__ == "__main__":
    main() 