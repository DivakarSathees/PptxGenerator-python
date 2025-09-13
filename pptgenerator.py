from copy import deepcopy
import json
import requests
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import PP_PLACEHOLDER


def replace_placeholders(slide, data):
    """Replace {title}, {content}, {notes} placeholders in a slide"""
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        # print(shape.text_frame)
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                print(">>", run.text)
                txt = run.text.strip()

                if txt == "{title}" and "title" in data:
                    run.text = data["title"]
                if txt == "{content}" and "content" in data:
                    tf = shape.text_frame
                    # Remove only the placeholder text
                    run.text = ""
                    # Keep the first paragraph as template
                    first_para = para
                    for idx, point in enumerate(data["content"]):
                        # print("->", point)
                        # print("P:", first_para.text)
                        if idx == 0:
                            p = first_para
                            p.text = point
                        else:
                            p = tf.add_paragraph()
                            p.text = point
                            p.level = 0 
                        # p = para
                        # p.text = point
                        # p.bullet = True

                        # Enable bullet
                        p.font.name = "Calibri"
                        p.font.size = Pt(22)
                        # p.space_after = Pt(6)
                        # p.bullet = True
                        # if first_para.runs:
                        #     p.font.name = first_para.runs[0].font.name
                        #     p.font.size = first_para.runs[0].font.size
                        p.space_after = Pt(6)

                        # Proper bullet setting
                        p._element.get_or_add_pPr().get_or_add_defRPr()  # ensures default run properties exist
                        # p._element.get_or_add_pPr().get_or_add_buNone() 
        # text = shape.text.strip()
        # if "{title}" in text and "title" in data:
        #     shape.text = data["title"]
        # if "{content}" in text and "content" in data:
        #     shape.text = "\n".join(data["content"])
        # if "{notes}" in text and "notes" in data:
        #     if slide.notes_slide is None:
        #         slide.notes_slide
        #     if slide.notes_slide is not None:
        #         slide.notes_slide.notes_text_frame.text = data["notes"]

    # Handle {image}
    if "image_url" in data:
        try:
            response = requests.get(data["image_url"])
            if response.status_code == 200:
                image_stream = BytesIO(response.content)
                slide.shapes.add_picture(image_stream, Inches(5), Inches(2), width=Inches(4))
        except Exception as e:
            print(f"⚠️ Could not add image: {e}")

def duplicate_slide(prs, slide):
    """Duplicate a slide but exclude placeholders like 'Click to add title'"""
    slide_layout = slide.slide_layout
    new_slide = prs.slides.add_slide(slide_layout)

    # Remove all placeholders from new slide
    for shape in list(new_slide.shapes):
        if shape.is_placeholder:
            sp = shape.element
            sp.getparent().remove(sp)

    # Copy only non-placeholder shapes from original slide
    for shape in slide.shapes:
        # if shape.is_placeholder:
        #     continue
        new_el = deepcopy(shape.element)
        new_slide.shapes._spTree.insert_element_before(new_el, 'p:extLst')

    return new_slide

def build_ppt(template_path, json_path, output_path, temp_path):
    with open(json_path, "r") as f:
        slides_json = json.load(f)[0]["slides"]

    prs1 = Presentation(template_path)

    # Template may have only 4-5 slides, JSON may have 10+
    # We'll cycle through template slides, and clone when needed
    template_slide_count = len(prs1.slides)

    for idx, slide_data in enumerate(slides_json):
        if idx < template_slide_count: # Use existing template slide
            slide = prs1.slides[idx] 
        else:
            # Duplicate last template slide if we run out
            template_slide = prs1.slides[-1]
            # xml_slides = prs.slides._sldIdLst
            # new_slide = prs.slides.add_slide(template_slide.slide_layout)
            # slide = prs.slides[-1]
            slide = duplicate_slide(prs1, template_slide)
    # save the presentation after adding all slides
    prs1.save(temp_path)
    prs = Presentation(temp_path)
    template_slide_count1 = len(prs.slides)
    
    for idx, slide_data in enumerate(slides_json):
        if idx < template_slide_count1: # Use existing template slide
            slide = prs.slides[idx] 
        # else:
        #     # Duplicate last template slide if we run out
        #     template_slide = prs.slides[-1]
        #     # xml_slides = prs.slides._sldIdLst
        #     # new_slide = prs.slides.add_slide(template_slide.slide_layout)
        #     # slide = prs.slides[-1]
        #     slide = duplicate_slide(prs, template_slide)


        replace_placeholders(slide, slide_data)

    prs.save(output_path)
    print(f"✅ Final PPT created: {output_path}")

if __name__ == "__main__":
    build_ppt("template_iamneo.pptx", "slides.json", "Cloud_Trends_2025.pptx", "temp.pptx")
