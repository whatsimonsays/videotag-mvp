import requests
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("download_videos")

def download_sample_videos():
    """Download sample videos for testing."""
    
    # Sample video URLs (small, free videos)
    sample_videos = {
        "sample_bunny_5mb.mp4": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4",
        "sample_bunny_2mb.mp4":   "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_2mb.mp4",
        "sample_bunny_1mb.mp4":   "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"
    }
    
    for filename, url in sample_videos.items():
        if not os.path.exists(filename):
            logger.info(f"Downloading {filename} from {url}...")
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Downloaded {filename}")
            except Exception as e:
                logger.error(f"Failed to download {filename}: {e}")
        else:
            logger.info(f"{filename} already exists")

if __name__ == "__main__":
    download_sample_videos() 