from bson import ObjectId
import certifi
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import gridfs
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
import requests
import json
import demjson3  # pip install demjson3
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT
from pptx.dml.color import RGBColor
from io import BytesIO
import re
from dotenv import load_dotenv
from copy import deepcopy
from groq import Groq
from pptgenerator import build_ppt, get_ppt_from_mongodb, store_ppt_in_mongodb
import os
load_dotenv()


uri = os.getenv("MONGODB_URI")  # example: mongodb+srv://...
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client["ppt_database"]
fs = gridfs.GridFS(db)

# ------------------ Groq Client Setup ------------------ #
# Initialize Groq client with your API key
api_key = os.getenv("GROQ_API_KEY")
client = Groq(
    api_key = api_key
)

# ------------------ Input Schema ------------------ #
class SlideRequest(BaseModel):
    title: str
    slides: int

# ------------------ FastAPI app ------------------ #
origins = [
    "http://localhost:4200",   # Angular dev server
    "http://127.0.0.1:4200",
    # Add your deployed frontend URL here when hosting Angular
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],       # GET, POST, PUT, DELETE...
    allow_headers=["*"],
)

# ------------------ Groq AI Call ------------------ #
def call_groq_ai_system(user_input: str):
    """
    Calls Groq AI endpoint with system/user input and returns JSON slides.
    Replace 'YOUR_GROQ_API_KEY' and endpoint URL with your actual account details.
    """
    chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional presentation writer. Produce a JSON array of slides for the given topic. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            # model="llama-3.3-70b-versatile",
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
        )
    
    # Extract the AI-generated content
    try:
        ai_content = chat_completion.choices[0].message.content
    except (AttributeError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Invalid Groq AI response structure: {e}")

    # Extract JSON array substring
    match = re.search(r"(\[.*\])", ai_content, re.S)
    if not match:
        raise HTTPException(status_code=500, detail="Could not find JSON array in AI output")

    json_str = match.group(1)

    # --- Sanitize AI output ---
    # 1. Escape unescaped backslashes
    json_str = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_str)

    # 2. Remove trailing commas before closing brackets/braces
    json_str = re.sub(r',(\s*[\]\}])', r'\1', json_str)

    # 3. Ensure all quotes inside strings are escaped
    # (optional but safer if AI inserts quotes)
    # json_str = re.sub(r'(?<!\\)"', r'\"', json_str)  # use only if needed

    # --- Parse JSON robustly ---
    try:
        # Use demjson3 which can handle non-strict JSON from AI
        slides = demjson3.decode(json_str)
        if not isinstance(slides, list):
            raise HTTPException(status_code=500, detail="AI output is not a JSON array")
        return slides
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI JSON output: {e}")
# ------------------ API Endpoint ------------------ #
@app.post("/generate-ppt-slides/")
def generate_ppt_slides(request: List[SlideRequest]):
    if not request:
        raise HTTPException(status_code=400, detail="No input provided")
    
    # Use first item for simplicity
    topic = request[0].title
    slide_count = request[0].slides

    # user_prompt = f"Topic: {topic}\nProduce up to {slide_count} slides. Return only a valid JSON array where each slide is an object with fields: title, content (array), code (optional), notes (optional), image_url (optional)."
    user_prompt = f"""Topic: { topic }

Produce up to { slide_count } slides. Return only a valid JSON array where each slide is an object with the following fields:

- title (string) → concise slide heading
- content (array) → 5-6 bullet strings. Each bullet MUST have **keywords in bold** using Markdown.
  - Each bullet may optionally contain a "subpoints" field, which is an array of 1–3 short sub-bullet strings (with **keywords** in bold).
- code (optional string) → include only if a relevant detailed code snippet, syntax, or example improves the slide (code should be splited by \\n).
- notes (optional string) → speaker notes or explanation (1–3 sentences).
- image_url (optional string) → suggested image/diagram link if it would support the slide content.

The final output must be ONLY a valid JSON array with first array only with title, no extra text.

Return only a valid JSON array like:

[
  {{ "title": "Your Presentation Title" }},
  {{
    "title": "Introduction",
    "content": [
      {{"text": "**Definition** of AI", "subpoints": ["Focus on **machine learning**", "Includes **deep learning**"]}},
      {{"text": "Impact on **industries**"}}
    ],
    "code": "def example():\\n    return 'Hello, World!'",
    "notes": "Speaker notes go here.",
    "image_url": "https://example.com/image.png"
  }}
]"""

    slides_json = call_groq_ai_system(user_prompt)
    print("Slides JSON:", slides_json)  # Debugging line

    # Paths
    template_path = "template_iamneo.pptx"
    temp_path = "temp.pptx"
    output_path = f"{topic.replace(' ', '_')}.pptx"

    # Build PPT
    build_ppt(template_path, slides_json, output_path, temp_path)
    ppt_id = store_ppt_in_mongodb(output_path, Path(output_path).name)
    # get_ppt_from_mongodb(ppt_id, f"downloaded_{Path(output_path).name}")
    ppt_len = Presentation(output_path)
    # delete temp file and fiel in output path
    Path(temp_path).unlink(missing_ok=True)
    Path(output_path).unlink(missing_ok=True)

    return {"slides": slides_json}

    # return {"message": "PPT generated successfully", "output_file": output_path, "slides_count": len(ppt_len.slides), "ppt_id": str(ppt_id)}

@app.post("/generate-ppt/")
#  request in slide json format
def generate_ppt(request: List[dict]):
    if not request:
        raise HTTPException(status_code=400, detail="No input provided")

    slides_json = request
    topic = slides_json[0].get("title", "Generated_Presentation")
    # Paths
    template_path = "template_iamneo.pptx"
    temp_path = "temp.pptx"
    output_path = f"{topic.replace(' ', '_')}.pptx"

    # Build PPT
    build_ppt(template_path, slides_json, output_path, temp_path)
    ppt_id = store_ppt_in_mongodb(output_path, Path(output_path).name)
    # get_ppt_from_mongodb(ppt_id, f"downloaded_{Path(output_path).name}")
    ppt_len = Presentation(output_path)
    # delete temp file and fiel in output path
    Path(temp_path).unlink(missing_ok=True)
    Path(output_path).unlink(missing_ok=True)

    return {"message": "PPT generated successfully", "output_file": output_path, "slides_count": len(ppt_len.slides), "ppt_id": str(ppt_id)}

@app.get("/download/{ppt_id}")
def download_ppt(ppt_id: str):
    try:
        file_id = ObjectId(ppt_id)
        ppt_file = fs.get(file_id)

        return StreamingResponse(
            ppt_file,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename={ppt_file.filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"PPT not found: {e}")