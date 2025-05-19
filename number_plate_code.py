import cv2
import streamlit as st
import numpy as np
from PIL import Image
import easyocr

# Page setup
st.set_page_config(page_title="Car Number Plate Detector", layout="wide")
st.title("🚗 Number Plate Detection using Classical Image Processing")

st.markdown("""
Upload an image of a car, and this app will detect the number plate using edge detection, contour filtering,
and extract the text using EasyOCR If it clear..
""")

# Runtime modifications: sliders for threshold and filter size
st.sidebar.subheader("🛠 Adjust Parameters")
min_threshold = st.sidebar.slider('Min Threshold for Canny Edge Detection', 0, 100, 30, 1)
max_threshold = st.sidebar.slider('Max Threshold for Canny Edge Detection', 100, 300, 200, 1)
filter_size = st.sidebar.slider('Bilateral Filter Size', 1, 20, 11, 1)

# Upload image
uploaded_file = st.file_uploader("Upload a car image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Read and preprocess the image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply filters and edge detection with runtime-modified parameters
    blurred = cv2.bilateralFilter(gray, filter_size, 17, 17)
    edged = cv2.Canny(blurred, min_threshold, max_threshold)

    # Find contours
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

    number_plate_contour = None
    plate = None
    height = image.shape[0]
    lower_70_start = int(height * 0.3)  # Top 30% excluded

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)

            # Only process contours in the lower 70% of the image
            if y > lower_70_start:
                number_plate_contour = approx
                plate = image[y:y + h, x:x + w]
                break

    # Draw detected contour
    detected_img = image.copy()
    if number_plate_contour is not None:
        cv2.drawContours(detected_img, [number_plate_contour], -1, (0, 255, 0), 3)

    # Display processing steps
    st.subheader(" Processing Steps")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.image(image, caption="Original Image")
    with col2:
        st.image(gray, caption="Grayscale", clamp=True, channels="GRAY")
    with col3:
        st.image(edged, caption="Canny Edges", clamp=True, channels="GRAY")
    with col4:
        st.image(detected_img, caption="Detected Plate Outline")

    # OCR result
    st.subheader(" Detected Number Plate")
    if plate is not None:
        st.image(plate, caption="Detected Number Plate Region")
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(plate)
        if results:
            detected_text = " ".join([text[1] for text in results])
            st.success(f" Detected Text: {detected_text}")
        else:
            st.warning("No readable text detected on the plate.")
    else:
        st.warning("No number plate detected from the lower 70% of the image.")