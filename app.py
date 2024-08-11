from flask import Flask, request, render_template, jsonify
import fitz  # PyMuPDF
import os
from PIL import Image
import io
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def is_image_color(image):
    img_rgb = image.convert("RGB")
    img_array = np.array(img_rgb)

    # Convert image array to grayscale
    gray_image = image.convert("L")
    gray_array = np.array(gray_image)

    # Calculate the number of non-gray pixels
    color_pixels = np.sum(img_array[:, :, 0] != gray_array) + \
                   np.sum(img_array[:, :, 1] != gray_array) + \
                   np.sum(img_array[:, :, 2] != gray_array)
    
    total_pixels = img_array.size / 3  # Total number of pixels

    # Sensitivity threshold: Proportion of non-gray pixels to consider as color page
    color_threshold = 0.000000005  # More sensitive: detects smaller proportion of color pixels

    # Check if the proportion of non-gray pixels exceeds the threshold
    return (color_pixels / total_pixels) > color_threshold

def analyze_pdf(file_path):
    doc = fitz.open(file_path)
    color_pages = 0
    bw_pages = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()

        # Convert pixmap to PIL image
        img = Image.open(io.BytesIO(pix.tobytes()))

        if is_image_color(img):
            color_pages += 1
        else:
            bw_pages += 1

    return color_pages, bw_pages

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        color_pages, bw_pages = analyze_pdf(file_path)
        return jsonify({"color_pages": color_pages, "bw_pages": bw_pages})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
