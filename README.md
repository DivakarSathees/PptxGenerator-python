📊 AI-Powered PPT Generator

This project allows you to generate and edit PowerPoint presentations (PPTX) using AI models (Groq or Gemini), with support for slide editing, notes, reordering, and optional image scraping.

🚀 Features

🎨 Generate PPT from AI (Groq or Gemini).

✏️ Edit slides in-browser:

  Update titles, bullet points, sub-points.
  
  Edit or add presenter notes.
  
  Add/remove/reorder slides.

💻 Code slide support with title + snippet formatting.

📂 Save changes locally or download PPT.

🔍 Image scraping (optional) – fetches sample images from Google (⚠️ may have copyright issues).

🛠️ How to Use
1. Generate PPT

Select your AI model from the dropdown:

Groq → Fast, accurate, cost-effective.

Gemini → Creative, reasoning-focused, high-quality.

Enter the title of your presentation.

Choose the number of slides.

(Optional) Enable Scrape image from Google if you want AI-suggested images.

Click Generate PPT → wait while slides are created.

2. Edit Slides

Once slides are generated:

Use the sidebar to navigate or drag to reorder slides.

For each slide:

Title → Editable via input field.

Content → Update bullets and sub-points.

Code slides → Display formatted snippet only.

Notes → Editable text area.

Use buttons:

➕ Add Slide → Inserts a new slide.

🗑 Remove Slide → Deletes the current slide.

⬅ / ➡ Navigation controls → Move between slides.

💾 Save Changes → Persist edits.

3. Download PPT

Once you’re satisfied:

Click Download PPT → A .pptx file will be downloaded.

Open it in PowerPoint, Google Slides, or LibreOffice.

⚠️ What NOT to Do

❌ Don’t refresh while editing slides → all unsaved changes will be lost.

❌ Don’t input extremely long text in bullets (>600 chars) → will cause formatting issues.

❌ Don’t rely on scraped images without review → they may be copyrighted.

❌ Don’t remove slides[0] (first slide) → must always exist.

❌ Don’t use in production without .env setup:

MONGODB_URI (for storing PPTs).

GEMINI_API_KEY (for Gemini).

✅ Best Practices

Keep bullets short & clear (AI already chunks long text).

Use Groq for faster results, Gemini for creative presentations.

If using images, verify licensing before publishing.

Save edits frequently.

🧩 Tech Stack

Frontend → Angular (Slide editor, drag/drop, UI).

Backend → FastAPI (AI integration, PPTX generation).

DB → MongoDB + GridFS (store PPT files).

AI Models → Groq (llama-4-maverick) / Gemini (gemini-2.5-flash).
