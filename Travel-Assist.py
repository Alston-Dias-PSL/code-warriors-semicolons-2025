from flask import Flask, request, jsonify
from openai import OpenAI
import requests, os
import json
import csv
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)

# OpenAI API details
API_KEY = "xxxxxxxxxxxxxxxx"  # Replace with your OpenAI API key
URL = "https://zxz2wysnky.ap-south-1.awsapprunner.com"          # Replace with your base URL
MODEL = "amazon.nova-pro-v1:0-AI_Team"

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY, base_url=URL)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def extract_text_from_file(file_path):
    """
    Extracts and prints the content of a local file as a string.
    Supports: TXT, JSON, CSV, PDF, DOCX.
    """
    print ("checkpoint 1", file_path)
    if not os.path.isfile(file_path):
        print(f"File '{file_path}' not found.")
        return

    print ("checkpoint 2")
    ext = os.path.splitext(file_path)[-1].lower()

    print ("checkpoint 3")
    try:
        print ("checkpoint 4")
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
            print ("checkpoint 5")
        elif ext == '.json':
            print ("checkpoint 6")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.dumps(json.load(f), indent=4)
                print ("checkpoint 7")

        elif ext == '.csv':
            print ("checkpoint 8")
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                content = "\n".join([", ".join(row) for row in reader])
                print ("checkpoint 9")

        elif ext == '.pdf':
            print ("checkpoint 10")
            content = ""
            print ("checkpoint 11")
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                print ("checkpoint 12")
                for page in reader.pages:
                    content += page.extract_text() or ""
                    print ("checkpoint 13")

        elif ext == '.docx':
            print ("checkpoint 14")
            doc = Document(docx=file_path)
            print ("checkpoint 15")
            content = "\n".join([para.text for para in doc.paragraphs])
            print ("checkpoint 16")

        else:
            content = f"Unsupported file format: {ext}"

        # Print the extracted content
        print("\n--- Extracted Text ---\n")
        print ("checkpoint 17")
        return content

    except Exception as e:
        print(f"Error: {str(e)}")

# "/" Route
@app.route('/', methods=['GET'])
def home():
    """Default route that returns 'Hello World'."""
    return "Hello World"

# "/extract" Route
@app.route('/extract', methods=['POST'])
def extract_data():
    response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",  # You can choose the role here as needed
            "content": [
                {
                    "type": "text",
                    "text": "Extract the details of this image and reply in json format highlighting the costs and other impoertant fields and values"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://storage.googleapis.com/semicolons-bucket/demo-image.jpeg"
                    }
                }
            ]
        }
    ],
    max_tokens=1000
)
    return response.choices[0].message.content

@app.route('/pre_travel', methods=['POST'])
def pre_travel():
    FILE_PATH = "C:/Users/PranavNaik/Desktop/code-warriors-semicolons-2025/pre-travel-doc.docx"  # Replace with your local file path
    doc_data=extract_text_from_file(FILE_PATH)

    print(doc_data)

    prompt="""
        Extract the following travel details from the provided text and return the results in **JSON format**:
        1. **Date of Travel and Arrival:** Identify the travel date.
        2. **Time of Arrival and Departure:** Extract the approximate arrival and departure times, considering meeting schedules and events.
        3. **Source and Destination:** Identify the source (departure location) and destination (arrival location) of the travel.
        4. **Mode of Travel:** Assume the mode of travel is **by air** unless explicitly stated otherwise.
    
        I have shared the mail sent below
        {}
    """.format(doc_data)
    
    response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": prompt
        },
            ],
    max_tokens=1000
    )
    
    return response.choices[0].message.content




# Example usage



if __name__ == '__main__':
    app.run(debug=True)
