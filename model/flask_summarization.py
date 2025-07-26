from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
import requests
import io
import json
import argparse
import os
import sqlite3
# OCR Reader Singleton
# OCR Reader Singleton
_ocr_reader_instance = None

def get_ocr_reader():
    global _ocr_reader_instance
    if _ocr_reader_instance is None:
        _ocr_reader_instance = easyocr.Reader(['en'], gpu=False)
    return _ocr_reader_instance
from pdf2image import convert_from_bytes
import easyocr

# Use get_ocr_reader() to access the OCR reader singleton
# Initialize OCR (use singleton accessor only)

# FastAPI instance
app = FastAPI()

# Database path
DB_PATH = "summaries.db"

# Prompt template
PROMPT_TEMPLATE = """
You are a super-capable AI assistant. Given the following content, generate a concise summary that captures:
- Main ideas or steps
- Any tables or mathematical expressions described
- Hand-written annotations if present
Output ONLY valid JSON with:
{{"page": <page_number>, "summary": "<your_summary>"}}
Content:
"""

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_source TEXT,
            page INTEGER,
            summary TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_summary_to_db(pdf_source: str, summaries: list[dict]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for entry in summaries:
        cursor.execute(
            "INSERT INTO summaries (pdf_source, page, summary) VALUES (?, ?, ?)",
            (pdf_source, entry.get("page"), entry.get("summary"))
        )
    conn.commit()
    conn.close()

def call_ollama(prompt: str, model: str = "qwen2.5vl:7b") -> str:
    # Check available models
    try:
        models_res = requests.get("http://localhost:11434/api/tags", timeout=10)
        if models_res.status_code == 200:
            available_models = [m["name"] for m in models_res.json().get("models", [])]
            if model not in available_models:
                return f"[Error] Model '{model}' not found in Ollama. Available: {', '.join(available_models)}"
        else:
            return f"[Error] Could not fetch available models: {models_res.text}"
    except Exception as e:
        return f"[Exception] Error checking models: {str(e)}"

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        if res.status_code == 200:
            return res.json().get("response", "")
        else:
            return f"[Error] Ollama API returned status {res.status_code}: {res.text}"
    except Exception as e:
        return f"[Exception] Error calling Ollama API: {str(e)}"

# --- Summarization Logic ---
from PyPDF2 import PdfReader

def summarize_pdf_bytes(pdf_bytes: bytes, model: str = "qwen2.5vl:7b"):
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(pdf.pages)
    images = convert_from_bytes(pdf_bytes)
    summaries = []
    ocr_reader = get_ocr_reader()

    for i in range(num_pages):
        buf = io.BytesIO()
        images[i].save(buf, format="PNG")
        img_bytes = buf.getvalue()
        text_lines = ocr_reader.readtext(img_bytes, detail=0)
        text = "\n".join(text_lines)

        prompt = PROMPT_TEMPLATE + text + "\n"
        raw_response = call_ollama(prompt, model)

        try:
            summary = json.loads(raw_response)
        except json.JSONDecodeError:
            print(f"[Warning] Invalid JSON from model on page {i + 1}: {raw_response}")
            summary = {"page": i + 1, "summary": raw_response.strip()}
        if "page" not in summary:
            summary["page"] = i + 1
        summaries.append(summary)
    return summaries

class Summary(BaseModel):
    page: int
    summary: str

@app.get("/summarize", response_model=List[Summary])
async def api_summarize(pdf_url: str = Query(..., description="URL to a PDF"),
                        model: str = Query("qwen2.5vl:7b", description="Ollama model name")):
    try:
        resp = requests.get(pdf_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Could not download PDF: {resp.status_code}")
        summaries = summarize_pdf_bytes(resp.content, model)
        save_summary_to_db(pdf_url, summaries)
        return summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Could not download PDF: {resp.status_code}")
        summaries = summarize_pdf_bytes(resp.content, model)
        save_summary_to_db(pdf_url, summaries)
        return summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Summarize a PDF using Ollama")
    parser.add_argument('--pdf', help='Local file path or URL to PDF')
    parser.add_argument('--output', help='Path to save summary JSON')
    parser.add_argument('--model', default='qwen2.5vl:7b', help='Ollama model name')
    parser.add_argument('--serve', action='store_true', help='Run as FastAPI server')
    args = parser.parse_args()

    init_db()

    if args.serve:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif args.pdf and args.output:
        # Read PDF bytes
        from urllib.parse import urlparse
        parsed = urlparse(args.pdf)
        if parsed.scheme in ("http", "https"):
            r = requests.get(args.pdf)
            if r.status_code != 200:
                print(f"Error downloading PDF: {r.status_code}")
                exit(1)
            pdf_data = r.content
            source = args.pdf
        else:
            if not os.path.exists(args.pdf):
                print("Local file not found")
                exit(1)
            with open(args.pdf, 'rb') as f:
                pdf_data = f.read()
            source = os.path.abspath(args.pdf)

        # Summarize and save
        result = summarize_pdf_bytes(pdf_data, args.model)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # Save to DB
        save_summary_to_db(source, result)
        print(f"Summaries saved to {args.output} and database.")
    else:
        parser.print_help()