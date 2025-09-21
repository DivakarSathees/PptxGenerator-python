from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import requests
import json
import demjson3  # pip install demjson3
from pathlib import Path
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
app = FastAPI()

# ------------------ Helper Functions ------------------ #
# def add_bulleted_paragraph(tf, text, level=0):
#     """Add a paragraph with bullet support and Markdown formatting."""
#     p = tf.add_paragraph()
#     p.level = level
#     p.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
#     p.space_after = Pt(5)
#     tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
#     for token in tokens:
#         run = p.add_run()
#         if token.startswith("**") and token.endswith("**"):
#             run.text = token[2:-2]
#             run.font.bold = True
#         elif token.startswith("*") and token.endswith("*"):
#             run.text = token[1:-1]
#             run.font.italic = True
#         else:
#             run.text = token
#         run.font.name = "Calibri"
#         run.font.size = Pt(22)
#         run.font.color.rgb = RGBColor(0, 0, 0)
#     return p

# def replace_placeholders(slide, data):
#     """Replace placeholders in a slide."""
#     for shape in slide.shapes:
#         if not shape.has_text_frame:
#             continue

#         content_placeholder = any("{content}" in run.text for para in shape.text_frame.paragraphs for run in para.runs)
#         if content_placeholder and "content" in data:
#             tf = shape.text_frame
#             first_para = tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph()
#             original_level = first_para.level
#             # Clear extra paragraphs
#             for i in range(len(tf.paragraphs) - 1, 0, -1):
#                 tf.paragraphs[i]._element.getparent().remove(tf.paragraphs[i]._element)
#             first_para.clear()

#             content_items = []
#             for item in data["content"]:
#                 if isinstance(item, dict):
#                     main_text = item.get("text", "")
#                     if main_text:
#                         content_items.append(main_text)
#                     subpoints = item.get("subpoints", [])
#                     content_items.extend(subpoints)
#                 else:
#                     content_items.append(str(item))

#             if content_items:
#                 first_content = content_items[0]
#                 add_bulleted_paragraph(tf, first_content, original_level)
#                 for content_text in content_items[1:]:
#                     add_bulleted_paragraph(tf, content_text, original_level)
#             continue

#         for para in shape.text_frame.paragraphs:
#             for run in para.runs:
#                 txt = run.text.strip()
#                 if txt == "{title}" and "title" in data:
#                     run.text = data["title"]
#                 if txt == "{notes}" and "notes" in data:
#                     if slide.has_notes_slide:
#                         slide.notes_slide.notes_text_frame.text = data["notes"]
#                 if txt == "imageurl" and "image_url" in data:
#                     try:
#                         response = requests.get(data["image_url"])
#                         if response.status_code == 200:
#                             image_stream = BytesIO(response.content)
#                             left, top, width, height = shape.left, shape.top, shape.width, shape.height
#                             slide.shapes.add_picture(image_stream, left, top, width=width, height=height)
#                             sp = shape.element
#                             sp.getparent().remove(sp)
#                         else:
#                             run.text = f"status code: {response.status_code}"
#                     except Exception as e:
#                         run.text = f"⚠️ {e}"

# def duplicate_slide(prs, slide):
#     """Duplicate a slide while excluding placeholders."""
#     slide_layout = slide.slide_layout
#     new_slide = prs.slides.add_slide(slide_layout)
#     for shape in list(new_slide.shapes):
#         if shape.is_placeholder:
#             sp = shape.element
#             sp.getparent().remove(sp)
#     for shape in slide.shapes:
#         new_el = deepcopy(shape.element)
#         new_slide.shapes._spTree.insert_element_before(new_el, 'p:extLst')
#     return new_slide

# def build_ppt1(template_path, slides_json, output_path, temp_path):
#     prs1 = Presentation(template_path)
#     template_slide_count = len(prs1.slides)
#     for idx, _ in enumerate(slides_json):
#         if idx >= template_slide_count:
#             duplicate_slide(prs1, prs1.slides[-1])
#     prs1.save(temp_path)
#     prs = Presentation(temp_path)
#     for idx, slide_data in enumerate(slides_json):
#         if idx < len(prs.slides):
#             slide = prs.slides[idx]
#             replace_placeholders(slide, slide_data)
#     prs.save(output_path)
#     return output_path

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
@app.post("/generate-ppt/")
def generate_ppt(request: List[SlideRequest]):
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
    get_ppt_from_mongodb(ppt_id, f"downloaded_{Path(output_path).name}")
    ppt_len = Presentation(output_path)
    # delete temp file and fiel in output path
    Path(temp_path).unlink(missing_ok=True)
    Path(output_path).unlink(missing_ok=True)



    return {"message": "PPT generated successfully", "output_file": output_path, "slides_count": len(ppt_len.slides), "ppt_id": str(ppt_id)}
