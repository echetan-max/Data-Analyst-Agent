# Data-Analyst-Agent 

# [Data Analyst Agent](https://dataanalystai.streamlit.app/) using Llama-4 (Together.ai)

This is a powerful browser-based data analysis tool built with **Streamlit**, integrating **Together.ai's Llama-4 model** for intelligent document/question answering. It supports tabular, textual, PDF, DOCX, and even image data for OCR-based extraction.

---

## Features

- 🔍 Ask natural language questions about uploaded data
- 📊 Auto-generate visualizations (Histogram, Bar, Scatter)
- 📄 Supports `.csv`, `.xlsx`, `.pdf`, `.docx`, `.txt`, `.jpg/.png` with OCR
- 🦙 Powered by Llama-4 via [Together.ai](https://www.together.ai/)
- 💬 Uses `easyocr`, `fitz` (PyMuPDF), and `matplotlib` for backend processing
- 🧪 No database or backend needed — fully in-browser

---

## Requirements

Install all dependencies with:
pip install streamlit together pandas matplotlib python-docx openpyxl pymupdf easyocr pillow
## To run file in local pc 
streamlit run ml.py

