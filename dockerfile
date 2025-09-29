# Use Selenium base image with Chrome + Chromedriver
FROM selenium/standalone-chrome:latest

# Install Python
USER root
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["python3", "-m", "uvicorn", "ppt_generator_api:app", "--host", "0.0.0.0", "--port", "8000"]
