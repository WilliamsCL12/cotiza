import os
from flask import Flask, request, render_template, jsonify
import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np

app = Flask(__name__)

# Use the port from environment variable or default to 5000
PORT = int(os.environ.get("PORT", 5000))

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
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        color_pages, bw_pages = analyze_pdf(file_path)
        return jsonify({"color_pages": color_pages, "bw_pages": bw_pages})
    except Exception as e:
        return jsonify({"error": str(e)})

def analyze_pdf(file_path):
    doc = fitz.open(file_path)
    color_pages = 0
    bw_pages = 0
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image = Image.open(io.BytesIO(pix.tobytes()))
        np_image = np.array(image)
        
        if np_image[:, :, 3].max() == 255:  # If alpha channel is present
            np_image = np_image[:, :, :3]
        
        color_pixels = np.any(np_image[:, :, :3] != [0, 0, 0], axis=2)
        if np.any(color_pixels):
            color_pages += 1
        else:
            bw_pages += 1

    return color_pages, bw_pages

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
