from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from openai import OpenAI
import os
import json
import csv
from PyPDF2 import PdfReader
from docx import Document
import tempfile
import uvicorn
# Initialize FastAPI app
app = FastAPI()
# OpenAI API details
API_KEY = "sk-402e3d0136274443925a21"  # Replace with your OpenAI API key
BASE_URL = "https://zxz2wysnky.ap-south-1.awsapprunner.com"  # Replace with your base URL
MODEL = "amazon.nova-pro-v1:0-AI_Team"
# Initialize OpenAI client
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
# Allowed file extensions
ALLOWED_EXTENSIONS = {".txt", ".json", ".csv", ".pdf", ".docx"}
# Function to extract text from supported file types
def extract_text_from_file(file_path: str) -> str:
    """Extract text from TXT, JSON, CSV, PDF, or DOCX files."""
    ext = os.path.splitext(file_path)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.dumps(json.load(f), indent=4)
        elif ext == ".csv":
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                return "\n".join([", ".join(row) for row in reader])
        elif ext == ".pdf":
            content = ""
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    content += page.extract_text() or ""
            return content
        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
# Root Route
@app.get("/")
def home():
    """Default route that returns 'Hello World'."""
    return {"message": "Hello World"}
# Route to Extract Data from Image
@app.post("/extract")
def extract_data():
    """Extract details from an image using OpenAI API."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the details of this image and reply in JSON format highlighting costs and other important fields."},
                    {"type": "image_url", "image_url": {"url": "https://storage.googleapis.com/semicolons-bucket/demo-image.jpeg"}}
                ]
            }
        ],
        max_tokens=1000
    )
    return {"response": response.choices[0].message.content}
# Route to Extract Travel Details from an Uploaded File
@app.post("/pre_travel")
async def pre_travel(file: UploadFile = File(...)):
    """Extract travel details from an uploaded document."""
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
    # Save the file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_file.write(file.file.read())
        temp_file_path = temp_file.name
    # Extract text from the uploaded file
    doc_data = extract_text_from_file(temp_file_path)
    # Construct prompt
    prompt = f"""
    Extract the following travel details from the provided text and return the results in JSON format:
**Date of Travel and Arrival**
**Time of Arrival and Departure**
**Source and Destination**
**Mode of Travel** (Assume **by air** unless explicitly stated otherwise)
    Given Text:
    {doc_data}
    """
    # OpenAI API call
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    # Cleanup temp file
    os.remove(temp_file_path)
    return {"travel_details": response.choices[0].message.content}
# Run FastAPI with Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
