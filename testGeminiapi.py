from diffusers import StableDiffusionPipeline
import torch

# Load Stable Diffusion v1.5 (free on Hugging Face)
model_id = "runwayml/stable-diffusion-v1-5"

# Use GPU if available, else CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load pipeline
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16 if device=="cuda" else torch.float32)
pipe = pipe.to(device)

# Your text prompt
prompt = "A futuristic city skyline at sunset, ultra detailed, cinematic lighting"

# Generate image
image = pipe(prompt).images[0]

# Save to file
image.save("output.png")

print("✅ Image saved as output.png")
