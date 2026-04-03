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

    else:
        return jsonify({"error": "Unsupported file type"}), 400

    # 🧠 EXTRACTION

    # Name (full name)
    name_match = re.search(r'Name[:\- ]+([A-Za-z ]+)', text)
    name = name_match.group(1).strip() if name_match else None

    # Date
    date_match = re.search(r'\d{2}/\d{2}/\d{4}', text)
    date = date_match.group(0) if date_match else None

    # Amount (improved)
    amount_match = re.search(r'(?:Rs\.?|INR)?\s?\d+(?:,\d+)*(?:\.\d{2})?\s?INR?', text)
    amount = amount_match.group(0) if amount_match else None

    # Invoice
    invoice_match = re.search(r'INV\d+', text)
    invoice = invoice_match.group(0) if invoice_match else None

    # Sentiment
    if "paid" in text.lower():
        sentiment = "positive"
    elif "due" in text.lower():
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Document type
    document_type = "invoice" if invoice or amount else "general"

    # Summary
    summary = f"Name: {name if name else 'Unknown'}\nDate: {date if date else 'Unknown'}\nAmount: {amount if amount else 'Not Found'}"

    # Final Output
    result = {
        "fileName": file.filename,
        "summary": summary,
        "entities": {
            "name": name,
            "date": date,
            "amount": amount,
            "invoice_number": invoice
        },
        "sentiment": sentiment,
        "confidence_score": round(len(text) / 100, 2),
        "document_type": document_type
    }

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
