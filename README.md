Round 1A – Heading Detection
Repository Name: PDFHeadingExtractor

Project Overview
This project extracts headings from PDF documents using layout analysis, font-based heuristics, and optical character recognition (OCR). It is optimized for multilingual PDFs and works offline using PyMuPDF and Tesseract.

Features
Heading detection based on font size, weight, and structure

OCR support via pytesseract for image-based or scanned PDFs

Handles multilingual documents (e.g., Hindi, Telugu, English)

Outputs structured JSON with extracted headings

Technologies Used
Python

PyMuPDF

Pytesseract

PDF2Image

Langdetect

Input/Output
Input folder: /input (contains PDFs)

Output folder: /output (generates .json for each PDF)

Run using Docker
docker build -t pdfheadingextractor .
docker run --rm -v "$PWD/input:/app/input" -v "$PWD/output:/app/output" pdfheadingextractor
