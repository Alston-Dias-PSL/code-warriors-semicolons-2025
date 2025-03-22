from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import json
import csv
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document
from google.cloud import storage

app = FastAPI()

# OpenAI API details
API_KEY = "sk-402e3d0136274443925a21"  # Replace with your OpenAI API key
URL = "https://zxz2wysnky.ap-south-1.awsapprunner.com"  # Replace with your base URL
MODEL = "amazon.nova-pro-v1:0-AI_Team"

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY, base_url=URL)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Google Cloud Storage setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/PranavNaik/Desktop/code-warriors-semicolons-2025/vaulted-arcana.json"
BUCKET_NAME = "semicolons-bucket"


def upload_file_to_gcp(file: UploadFile, bucket_name: str):
    """Uploads the file to GCP and returns the public URL."""
    
    # Initialize GCP storage client
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Create a new blob (file) in the bucket
    blob = bucket.blob(file.filename)
    
    # Upload the file to the bucket
    blob.upload_from_file(file.file)

    # Make the file publicly accessible
    blob.make_public()

    # Get the public URL
    return blob.public_url


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """API endpoint to upload a file to GCP and return the public URL."""
    
    try:
        public_url = upload_file_to_gcp(file, BUCKET_NAME)
        
        return JSONResponse(content={
            "message": "File uploaded successfully!",
            "public_url": public_url
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def extract_text_from_file(file: UploadFile):
    """
    Extracts and prints the content of an uploaded file as a string.
    Supports: TXT, JSON, CSV, PDF, DOCX.
    """
    ext = os.path.splitext(file.filename)[-1].lower()
    content = ""

    try:
        if ext == '.txt':
            content = file.file.read().decode('utf-8')

        elif ext == '.json':
            content = json.dumps(json.load(file.file), indent=4)

        elif ext == '.csv':
            reader = csv.reader(file.file.read().decode('utf-8').splitlines())
            content = "\n".join([", ".join(row) for row in reader])

        elif ext == '.pdf':
            reader = PdfReader(file.file)
            content = "\n".join([page.extract_text() or "" for page in reader.pages])

        elif ext == '.docx':
            doc = Document(file.file)
            content = "\n".join([para.text for para in doc.paragraphs])

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")

        return content

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def home():
    """Default route that returns 'Hello World'."""
    return {"message": "Hello World"}


@app.post("/extract")
async def extract_data():
    """Extracts details from an image using OpenAI."""
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract the details of this image and reply in JSON format highlighting the costs and other important fields and values"
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
    
    return JSONResponse(content=response.choices[0].message.content)


@app.post("/pre_travel")
async def pre_travel(file: UploadFile = File(...)):
    """Extracts travel details from an uploaded file."""
    try:
        doc_data = extract_text_from_file(file)

        prompt = f"""
        Extract the following travel details from the provided text and return the results in **JSON format**:
        1. **Date of Travel and Arrival:** Identify the travel date.
        2. **Time of Arrival and Departure:** Extract the approximate arrival and departure times, considering meeting schedules and events.
        3. **Source and Destination:** Identify the source (departure location) and destination (arrival location) of the travel.
        4. **Mode of Travel:** Assume the mode of travel is **by air** unless explicitly stated otherwise.

        I have shared the mail sent below
        {doc_data}
        """

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return JSONResponse(content=response.choices[0].message.content)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
