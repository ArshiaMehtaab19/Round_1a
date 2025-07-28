Round 1A – Document Outline Extractor

**Challenge Theme: “Connecting the Dots Through Docs”
**Problem Statement
You’re given a PDF document — your job is to extract a structured outline including the Title, H1, H2, and H3 headings. The goal is to enable machines to understand the logical structure of documents the way humans do.

What Our Solution Does
Accepts PDFs (up to 50 pages)

Extracts:
Title
Headings with levels (H1, H2, H3)
Page number for each heading
Generates a structured JSON output like:
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
Approach
We combine PDF parsing, font size clustering, and layout analysis to detect headings accurately — even in multilingual documents.
PyMuPDF is used for layout-aware PDF parsing
Tesseract OCR handles scanned/multilingual pages (e.g., Hindi, Telugu)
Headings are detected based on:
Font size hierarchy
Font weight/style (bold, caps)
Spatial layout (top position, spacing)
Simple heuristics are used to classify heading levels

Libraries Used

pymupdf for PDF layout parsing
pytesseract for OCR
langdetect for language guessing
pdf2image for OCR fallback
numpy for clustering font sizes

Docker Setup
The solution is containerized using Docker and supports offline execution with no internet access.

🔧 Dockerfile Highlights
Platform: linux/amd64

Includes: Tesseract with English, Hindi, Telugu

Compatible with 8 CPU, 16GB RAM systems

Model size: <200MB

How to Build & Run (For Evaluation)
This matches the competition's "Expected Execution" section.

1. Build the Docker Image
docker build --platform linux/amd64 -t pdfheadingextractor:yourtag .
2. Run the Solution
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdfheadingextractor:yourtag
This will:

Read all PDFs from /app/input

Generate JSON files in /app/output (same name as PDFs)

Project Structure
├── Dockerfile
├── main.py
├── requirements.txt
├── input/                 # Input PDFs (mounted at runtime)
├── output/                # Output JSONs (mounted at runtime)
└── README.md


