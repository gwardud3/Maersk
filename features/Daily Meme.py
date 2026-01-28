import streamlit as st
import os
from PIL import Image

# ---------------- Resource path ----------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def daily_meme_app():
    st.header("🖼️ Image Viewer")

    image_name = "meme.png"  # change if needed
    image_path = os.path.join(ASSETS_DIR, image_name)

    if not os.path.exists(image_path):
        st.error(f"Image not found: {image_name}")
        return

    image = Image.open(image_path)

    st.image(
        image,
        caption=image_name,
        use_container_width=True
    )
