import requests
import json
import base64
import time
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("vidisnap_test")

class VidiSnapTester:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
        self.test_results = []
    
    def test_health(self):
        """Test the health endpoint."""
        logger.info("Testing health endpoint...")
        try:
            response = requests.get(f"{self.api_url}/health")
            if response.status_code == 200:
                logger.info("Health check passed")
                logger.info(f"   Response: {response.json()}")
                return True
            else:
                logger.info(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.info(f"Health check error: {e}")
            return False
    
    def test_video_processing(self, video_path):
        """Test video processing with a specific video file."""
        logger.info(f"\nTesting video processing: {video_path}")
        
        if not os.path.exists(video_path):
            logger.info(f"Video file not found: {video_path}")
            return False
        
        start_time = time.time()
        
        try:
            with open(video_path, 'rb') as f:
                files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
                response = requests.post(f"{self.api_url}/analyze", files=files)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Video processing successful!")
                logger.info(f"   Processing time: {processing_time:.2f} seconds")
                logger.info(f"   File size: {os.path.getsize(video_path) / 1024:.1f} KB")
                
                # Display labels
                logger.info("\nTop 3 Labels:")
                for i, label in enumerate(result['labels'], 1):
                    logger.info(f"   {i}. {label['label']} (confidence: {label['score']:.4f})")
                
                # Save thumbnail
                if result.get('thumbnail_b64'):
                    thumbnail_path = f"thumbnail_{os.path.splitext(os.path.basename(video_path))[0]}.jpg"
                    with open(thumbnail_path, 'wb') as f:
                        f.write(base64.b64decode(result['thumbnail_b64']))
                    logger.info(f"Thumbnail saved: {thumbnail_path}")
                
                self.test_results.append({
                    'video': video_path,
                    'success': True,
                    'processing_time': processing_time,
                    'labels': result['labels']
                })
                return True
            else:
                logger.info(f"Video processing failed: {response.status_code}")
                logger.info(f"   Error: {response.text}")
                self.test_results.append({
                    'video': video_path,
                    'success': False,
                    'error': response.text
                })
                return False
                
        except Exception as e:
            logger.info(f"Video processing error: {e}")
            self.test_results.append({
                'video': video_path,
                'success': False,
                'error': str(e)
            })
            return False
    
    def test_invalid_file(self):
        """Test with an invalid file type."""
        logger.info("\nTesting invalid file type...")
        
        # Create a dummy text file
        dummy_file = "dummy.txt"
        with open(dummy_file, 'w') as f:
            f.write("This is not a video file")
        
        try:
            with open(dummy_file, 'rb') as f:
                files = {'file': (dummy_file, f, 'text/plain')}
                response = requests.post(f"{self.api_url}/analyze", files=files)
            
            if response.status_code == 400:
                logger.info("Invalid file correctly rejected")
                logger.info(f"   Error: {response.json()}")
                return True
            else:
                logger.info(f"Invalid file not properly rejected: {response.status_code}")
                return False
                
        except Exception as e:
            logger.info(f"Invalid file test error: {e}")
            return False
        finally:
            # Clean up dummy file
            if os.path.exists(dummy_file):
                os.remove(dummy_file)
    
    def run_all_tests(self):
        """Run all tests."""
        logger.info("Starting VidiSnap API Tests")
        logger.info("=" * 50)
        
        # Test health first
        if not self.test_health():
            logger.info("Health check failed. Make sure the API is running.")
            return
        
        # Test with available video files
        video_files = [
            "test_video.mp4",
            "sample_bunny_1mb.mp4", 
            "sample_bunny_2mb.mp4",
            "sample_bunny_5mb.mp4"
        ]
        
        for video_file in video_files:
            if os.path.exists(video_file):
                self.test_video_processing(video_file)
            else:
                logger.info(f"Skipping {video_file} (not found)")
        
        # Test invalid file
        self.test_invalid_file()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)
        
        successful_tests = [r for r in self.test_results if r.get('success', False)]
        failed_tests = [r for r in self.test_results if not r.get('success', False)]
        
        logger.info(f"Successful tests: {len(successful_tests)}")
        logger.info(f"Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            avg_time = sum(r['processing_time'] for r in successful_tests) / len(successful_tests)
            logger.info(f"Average processing time: {avg_time:.2f} seconds")
        
        # Show all detected labels
        all_labels = []
        for result in successful_tests:
            all_labels.extend(result['labels'])
        
        if all_labels:
            logger.info("\nAll detected labels:")
            label_counts = {}
            for label in all_labels:
                label_name = label['label']
                label_counts[label_name] = label_counts.get(label_name, 0) + 1
            
            for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   {label}: {count} times")

def main():
    """Main test function."""
    tester = VidiSnapTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 