const fs = require("fs");
const PptxGenJS = require("pptxgenjs");

/**
 * Add formatted text with support for **bold** and *italic* markers.
 */
function parseFormattedText(text) {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g).filter(Boolean);
  return parts.map((part) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return { text: part.slice(2, -2), options: { bold: true } };
    } else if (part.startsWith("*") && part.endsWith("*")) {
      return { text: part.slice(1, -1), options: { italic: true } };
    } else {
      return { text: part };
    }
  });
}

/**
 * Replace placeholders in a slide
 */
async function replacePlaceholders(slide, data) {
  if (data.title) {
    slide.addText(data.title, { x: 0.5, y: 0.3, w: "90%", fontSize: 28, bold: true });
  }

  if (data.content) {
    data.content.forEach((item, idx) => {
      const y = 1.2 + idx * 0.6;
      slide.addText(parseFormattedText(item.text), {
        x: 0.7,
        y,
        fontSize: 22,
        bullet: true,
        fontFace: "Calibri",
      });
    });
  }

  if (data.code) {
    slide.addText(data.code, {
      x: 0.5,
      y: 4.5,
      w: 8,
      h: 2,
      fontFace: "Consolas",
      fontSize: 18,
      color: "000000",
      fill: { color: "e6e6e6" },
    });
  }

  if (data.notes) {
    slide.addNotes(data.notes);
  }

  if (data.image_url) {
    try {
      const response = await fetch(data.image_url); // built-in fetch
      if (response.ok) {
        const buffer = await response.arrayBuffer();
        const base64 = Buffer.from(buffer).toString("base64");

        slide.addImage({
          data: `data:image/png;base64,${base64}`,
          x: 5.5,
          y: 1.0,
          w: 3.5,
          h: 2.5,
        });
      }
    } catch (err) {
      console.warn("⚠️ Could not add image:", err);
    }
  }
}

/**
 * Build PPT from JSON
 */
async function buildPpt(templateJsonPath, outputPath) {
  const raw = fs.readFileSync(templateJsonPath, "utf-8");
  const slidesJson = JSON.parse(raw)[0].slides;

  const pptx = new PptxGenJS();

  for (let i = 0; i < slidesJson.length; i++) {
    const slide = pptx.addSlide();
    await replacePlaceholders(slide, slidesJson[i]);
  }

  await pptx.writeFile({ fileName: outputPath });
  console.log(`✅ Final PPT created: ${outputPath}`);
}

// Run
(async () => {
  await buildPpt("slides.json", "Cloud_Trends_2025.pptx");
})();
