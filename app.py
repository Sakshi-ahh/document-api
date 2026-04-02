from flask import Flask, request, jsonify
import pdfplumber
import pytesseract
from PIL import Image
import re

app = Flask(__name__)

API_KEY = "123456"

@app.route('/analyze', methods=['POST'])
def analyze():
    # 🔐 API KEY CHECK
    key = request.headers.get('Authorization') or request.headers.get('api-key')
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    # 📂 FILE CHECK
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    if file.filename == "":
        return jsonify({"error": "Empty file"}), 400

    text = ""

    # 📄 PDF HANDLING
    if file.filename.endswith('.pdf'):
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except:
            return jsonify({"error": "Error reading PDF"}), 500

    # 🖼 IMAGE HANDLING
    elif file.filename.endswith(('.png', '.jpg', '.jpeg')):
        try:
            image = Image.open(file)
            text = pytesseract.image_to_string(image)
        except:
            return jsonify({"error": "Error reading image"}), 500

    # ❌ UNSUPPORTED FILE
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    # 🧠 DATA EXTRACTION (SMART PART)
    name = re.findall(r'Name[:\- ]+(.*)', text)
    date = re.findall(r'\d{2}/\d{2}/\d{4}', text)
    amount = re.findall(r'\d+\s?INR', text)
    invoice = re.findall(r'INV\d+', text)

    # 📊 RESULT
   result = {
    "fileName": file.filename,

    "summary": text[:150],

    "entities": {
        "name": name[0] if name else None,
        "date": date[0] if date else None,
        "amount": amount[0] if amount else None,
        "invoice_number": invoice[0] if invoice else None
    },

    "sentiment": "neutral"
}

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
