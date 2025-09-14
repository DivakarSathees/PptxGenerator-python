from copy import deepcopy
import json
import re
import requests
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE, PP_PARAGRAPH_ALIGNMENT

# ------------------ Helper Functions ------------------ #
def add_bulleted_paragraph(tf, text, level=0):
    """
    Add a paragraph with bullet support and bold/italic formatting.
    level: 0 = main bullet, 1 = sub-bullet
    """
    p = tf.add_paragraph()
    p.level = level
    p.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
    p.space_after = Pt(5)

    # Temporarily add text for formatting
    p.text = ""
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
    for token in tokens:
        run = p.add_run()
        if token.startswith("**") and token.endswith("**"):
            run.text = token[2:-2]
            run.font.bold = True
        elif token.startswith("*") and token.endswith("*"):
            run.text = token[1:-1]
            run.font.italic = True
        else:
            run.text = token
        run.font.name = "Calibri"
        run.font.size = Pt(22)
        run.font.color.rgb = RGBColor(0, 0, 0)

    return p

# ------------------ Placeholder Replacement ------------------ #
def replace_placeholders(slide, data):
    """Replace placeholders in a slide."""
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue

        # Check if this text frame contains the {content} placeholder
        content_placeholder_found = False
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if run.text.strip() == "{content}":
                    content_placeholder_found = True
                    break
            if content_placeholder_found:
                break
        
        if content_placeholder_found and "content" in data:
            # Handle content replacement specially to maintain bullet formatting
            tf = shape.text_frame
            
            # Get the original bullet formatting from the first paragraph
            first_para = tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph()
            original_level = first_para.level
            
            # Clear all paragraphs except the first one
            for i in range(len(tf.paragraphs) - 1, 0, -1):
                tf.paragraphs[i]._element.getparent().remove(tf.paragraphs[i]._element)
            
            # Clear the first paragraph's text but keep its formatting
            first_para.clear()
            
            # Process content - treat each content item as a separate bullet point
            if data["content"]:
                content_items = []
                
                # Flatten content structure - each main text becomes a bullet point
                for item in data["content"]:
                    if isinstance(item, dict):
                        main_text = item.get("text", "")
                        if main_text:
                            content_items.append(main_text)
                        # Add subpoints as separate items with increased indentation
                        subpoints = item.get("subpoints", [])
                        content_items.extend(subpoints)
                    else:
                        # Handle simple string items
                        content_items.append(str(item))
                
                # Add first content item to the existing first paragraph
                if content_items:
                    first_content = content_items[0]
                    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', first_content)
                    for token in tokens:
                        run = first_para.add_run()
                        if token.startswith("**") and token.endswith("**"):
                            run.text = token[2:-2]
                            run.font.bold = True
                        elif token.startswith("*") and token.endswith("*"):
                            run.text = token[1:-1]
                            run.font.italic = True
                        else:
                            run.text = token
                        run.font.name = "Calibri"
                        run.font.size = Pt(22)
                        run.font.color.rgb = RGBColor(0, 0, 0)
                    
                    # Set the original level for first paragraph
                    first_para.level = original_level
                    
                    # Add remaining content items as new paragraphs with same formatting
                    for content_text in content_items[1:]:
                        new_para = tf.add_paragraph()
                        new_para.level = original_level
                        new_para.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
                        new_para.space_after = Pt(5)
                        
                        tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', content_text)
                        for token in tokens:
                            run = new_para.add_run()
                            if token.startswith("**") and token.endswith("**"):
                                run.text = token[2:-2]
                                run.font.bold = True
                            elif token.startswith("*") and token.endswith("*"):
                                run.text = token[1:-1]
                                run.font.italic = True
                            else:
                                run.text = token
                            run.font.name = "Calibri"
                            run.font.size = Pt(22)
                            run.font.color.rgb = RGBColor(0, 0, 0)
            
            continue  # Skip the normal processing for this shape
        
        # Normal placeholder processing for other placeholders
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                txt = run.text.strip()
                print(">>", run.text)

                # --- Title ---
                if txt == "{title}" and "title" in data:
                    run.text = data["title"]

                # --- Code ---
                if txt == "{code}":
                    if "code" in data:
                        tf = shape.text_frame
                        tf.clear()
                        tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
                        p = tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph()
                        p.clear()
                        run = p.add_run()
                        run.text = data["code"]
                        run.font.name = "Consolas"
                        run.font.size = Pt(20)
                        run.font.color.rgb = RGBColor(0, 0, 0)
                        fill = shape.fill
                        fill.solid()
                        fill.fore_color.rgb = RGBColor(230, 230, 230)
                        p.level = 0
                    else:
                        run.text = ""

                # --- Notes ---
                if txt == "{notes}" and "notes" in data:
                    if slide.has_notes_slide:
                        slide.notes_slide.notes_text_frame.text = data["notes"]

                # --- Image ---
                if txt == "imageurl":
                    if "image_url" in data:
                        try:
                            response = requests.get(data["image_url"])
                            if response.status_code == 200:
                                image_stream = BytesIO(response.content)
                                run.text = ""
                                left, top, width, height = shape.left, shape.top, shape.width, shape.height
                                slide.shapes.add_picture(image_stream, left, top, width=width, height=height)
                                # remove original placeholder
                                sp = shape.element
                                sp.getparent().remove(sp)
                            else:
                                run.text = f"status code: {response.status_code} -> {data["image_url"]}"
                        except Exception as e:
            
                            print(f"⚠️ Could not add image: {e}")
                    else:
                        run.text = ""

# ------------------ Slide Duplication ------------------ #
def duplicate_slide(prs, slide):
    """Duplicate a slide while excluding placeholders."""
    slide_layout = slide.slide_layout
    new_slide = prs.slides.add_slide(slide_layout)

    # remove placeholders
    for shape in list(new_slide.shapes):
        if shape.is_placeholder:
            sp = shape.element
            sp.getparent().remove(sp)

    # copy original shapes
    for shape in slide.shapes:
        new_el = deepcopy(shape.element)
        new_slide.shapes._spTree.insert_element_before(new_el, 'p:extLst')

    return new_slide

# ------------------ Build PPT ------------------ #
def build_ppt(template_path, json_path, output_path, temp_path):
    with open(json_path, "r") as f:
        slides_json = json.load(f)[0]["slides"]

    prs1 = Presentation(template_path)
    template_slide_count = len(prs1.slides)

    # Ensure enough slides
    for idx, _ in enumerate(slides_json):
        if idx >= template_slide_count:
            duplicate_slide(prs1, prs1.slides[-1])

    prs1.save(temp_path)
    prs = Presentation(temp_path)

    for idx, slide_data in enumerate(slides_json):
        if idx < len(prs.slides):
            slide = prs.slides[idx]
            replace_placeholders(slide, slide_data)

    prs.save(output_path)
    print(f"✅ Final PPT created: {output_path}")

# ------------------ Main ------------------ #
if __name__ == "__main__":
    build_ppt("template_iamneo.pptx", "slides.json", "Cloud_Trends_2025.pptx", "temp.pptx")