import streamlit as st
import requests
import base64
from PIL import Image
import io
import time
import os

# Page config
st.set_page_config(
    page_title="VidiSnap - Quick Demo",
    page_icon="🎬",
    layout="wide"
)

# Configuration
BACKEND_URL = os.getenv('VIDISNAP_BACKEND_URL', 'http://localhost:8000')
TIMEOUT_SECONDS = int(os.getenv('VIDISNAP_TIMEOUT', '120'))

# Title and description
st.title("VidiSnap – Quick Demo")
st.markdown("Upload a video to get AI-powered classification of its first frame.")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a video file",
    type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'],
    help="Select a video file to analyze"
)

# Process button
if uploaded_file is not None:
    if st.button("Process Video", type="primary"):
        with st.spinner("Classifying video..."):
            try:
                # Prepare the file for upload
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'video/mp4')}
                
                # Send request to FastAPI
                response = requests.post(
                    f"{BACKEND_URL}/process",
                    files=files,
                    timeout=TIMEOUT_SECONDS
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display thumbnail
                    if result.get('thumbnail_b64'):
                        thumbnail_data = base64.b64decode(result['thumbnail_b64'])
                        image = Image.open(io.BytesIO(thumbnail_data))
                        st.image(image, caption="First frame", use_container_width=False)
                    
                    # Display labels
                    if result.get('labels'):
                        st.subheader("Top-3 predictions")
                        
                        # Create table data
                        table_data = []
                        for label_info in result['labels']:
                            label = label_info['label']
                            score = label_info['score'] * 100 
                            table_data.append([label, f"{score:.2f}%"])
                        
                        # Display as table
                        st.table(table_data)
                        
                else:
                    st.error(f"Processing failed: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try with a smaller video file.")
            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to the processing service at {BACKEND_URL}. Make sure it's running and accessible.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("*Powered by FastAPI and Hugging Face Transformers*") 