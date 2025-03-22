from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from openai import OpenAI
import os
import json, requests
import csv
from PyPDF2 import PdfReader
from docx import Document
import uvicorn
from google.cloud import storage

# Initialize FastAPI app
app = FastAPI()
# OpenAI API details
API_KEY = "sk-402e3d0136274443925a21"  # Replace with your OpenAI API key
BASE_URL = (
    "https://zxz2wysnky.ap-south-1.awsapprunner.com"  # Replace with your base URL
)
MODEL = "amazon.nova-pro-v1:0-AI_Team"

# Root Route
@app.get("/")
def home():
    """Default route that returns 'Hello World'."""
    return {"message": "Hello Judges"}

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Allowed file extensions for pre travel
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

# Route to Extract Data from Image
gcp_secret_path = "vaulted-arcana.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), gcp_secret_path)
BUCKET_NAME = "semicolons-bucket"

def upload_file_to_gcp(file: UploadFile, bucket_name):
    """Uploads the file to GCP and makes it publicly accessible"""
    
    # Initialize GCP storage client
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Create a new blob (file) in the bucket
    blob = bucket.blob(file.filename)

    file_bytes = file.file.read()

    blob.upload_from_string(file_bytes, content_type=file.content_type)

    # Upload the file to the bucket
    #blob.upload_from_file(file)

    # Make the file publicly accessible
    blob.make_public()

    # Get the public URL
    public_url = blob.public_url

    return public_url

# To download file from GCP
def download_file_from_gcp_url(file_url, save_path):
    """
    Downloads a file from a GCP public URL and saves it locally.

    Parameters:
    - file_url (str): The GCP public URL of the file.
    - save_path (str): The local path where the file will be saved.

    Returns:
    - str: The path where the file is saved.
    """
    save_path=os.path.join(os.getcwd(), save_path)
    print("File URL: ", file_url, " save Path: ", os.path.join(os.getcwd(), save_path))
    try:
        print("checkpoint: ", file_url)
        response = requests.get(file_url)
        print("response: ", response)
        if response.status_code == 200:
            print("checkpoint 2")
            with open(save_path, "wb") as file:
                file.write(response.content)
                print("checkpoint 3")
                doc_data = extract_text_from_file(save_path)
            print("checkpoint 5")
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
            print("prompt1", prompt)
            return prompt
        else:
            raise Exception(f"Failed to download file. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")
        return None
    

# @app.post("/extract")
# def extract_data():
#     """Extract details from an image using OpenAI API."""
#     response = client.chat.completions.create(
#         model=MODEL,
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "text",
#                         "text": "Extract the details of this image and reply in JSON format highlighting costs and other important fields.",
#                     },
#                     {
#                         "type": "image_url",
#                         "image_url": {
#                             "url": "https://storage.googleapis.com/semicolons-bucket/demo-image.jpeg"
#                         },
#                     },
#                 ],
#             }
#         ],
#         max_tokens=1000,
#     )
#     return {"response": response.choices[0].message.content}


# # Route to Extract Travel Details from an Uploaded File


@app.post("/pre_travel")
async def pre_travel(file: UploadFile = File(...)):
    """Extract travel details from an uploaded document."""
    ext = os.path.splitext(file.filename)[-1].lower()
    print("FILE: ", file)
    public_url = upload_file_to_gcp(file, bucket_name=BUCKET_NAME)
    print("public_url-last: ", public_url)
    if ext not in ALLOWED_EXTENSIONS:
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
                            "url": public_url
                        }
                    }
                ]   
            }
        ],
        max_tokens=1000
    )
        return {"travel_details": response.choices[0].message.content}
    else:
        print("public_url-last: ", public_url)
        prompt = download_file_from_gcp_url(public_url, save_path=file.filename)
        print("prompt", prompt)
        # OpenAI API call
        response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=1000
        )
        return response.choices[0].message.content
        

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
