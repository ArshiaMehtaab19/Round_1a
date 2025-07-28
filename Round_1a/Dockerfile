# Use lightweight Python image
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Install Tesseract OCR and essential language packs including Hindi
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-jpn \
    tesseract-ocr-spa \
    tesseract-ocr-fra \
    tesseract-ocr-tel \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-noto-extra \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Copy all files to container
COPY . .

# Install required Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Run the script
CMD ["python", "main.py"]
