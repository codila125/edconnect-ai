from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
import requests, io, json, argparse, os
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import easyocr
import sqlite3
from datetime import datetime
from typing import List, Optional

# Initialize OCR
ocr_reader = easyocr.Reader(['en'], gpu=False)

# FastAPI instance
app = FastAPI()

# Database setup
DATABASE_PATH = "pdf_summaries.db"

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create summaries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_url TEXT NOT NULL,
            model TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create documents table for tracking processed PDFs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_url TEXT UNIQUE NOT NULL,
            model TEXT NOT NULL,
            total_pages INTEGER NOT NULL,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
    return conn

# Unified prompt for summarization
PROMPT_TEMPLATE = """
You are a super-capable AI assistant. Given the following content, generate a concise summary that captures:
- Main ideas or steps
- Any tables or mathematical expressions described
- Hand-written annotations if present
Output ONLY valid JSON with:
{{"page": <page_number>, "summary": "<your_summary>"}}
Content:
"""

# Function to call Ollama via REST API
def call_ollama(prompt: str, model: str = "qwen2.5vl:7b") -> str:
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        if res.status_code == 200:
            return res.json().get("response", "")
        else:
            return f"[Error {res.status_code}] {res.text}"
    except Exception as e:
        return f"[Exception] {str(e)}"

# PDF summarization logic with database storage
def summarize_pdf_bytes_with_db(pdf_bytes: bytes, pdf_url: str, model: str = "qwen2.5vl:7b") -> list[dict]:
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    summaries = []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if PDF already processed
    cursor.execute("SELECT * FROM documents WHERE pdf_url = ?", (pdf_url,))
    existing_doc = cursor.fetchone()
    
    if existing_doc:
        # Return existing summaries
        cursor.execute("SELECT page_number, summary FROM summaries WHERE pdf_url = ? ORDER BY page_number", (pdf_url,))
        existing_summaries = cursor.fetchall()
        conn.close()
        return [{"page": row["page_number"], "summary": row["summary"]} for row in existing_summaries]

    # Process new PDF
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            images = convert_from_bytes(pdf_bytes, first_page=i, last_page=i)
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            img_bytes = buf.getvalue()
            text_lines = ocr_reader.readtext(img_bytes, detail=0)
            text = "\n".join(text_lines)

        prompt = PROMPT_TEMPLATE + text + "\n"
        raw_response = call_ollama(prompt, model)

        try:
            summary = json.loads(raw_response)
        except json.JSONDecodeError:
            summary = {"page": i, "summary": raw_response.strip()}

        summaries.append(summary)
        
        # Store in database
        cursor.execute(
            "INSERT INTO summaries (pdf_url, model, page_number, summary) VALUES (?, ?, ?, ?)",
            (pdf_url, model, i, summary["summary"])
        )

    # Store document record
    cursor.execute(
        "INSERT INTO documents (pdf_url, model, total_pages) VALUES (?, ?, ?)",
        (pdf_url, model, len(pdf.pages))
    )
    
    conn.commit()
    conn.close()
    
    return summaries

# Original function for backward compatibility
def summarize_pdf_bytes(pdf_bytes: bytes, model: str = "qwen2.5vl:7b") -> list[dict]:
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    summaries = []

    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            images = convert_from_bytes(pdf_bytes, first_page=i, last_page=i)
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            img_bytes = buf.getvalue()
            text_lines = ocr_reader.readtext(img_bytes, detail=0)
            text = "\n".join(text_lines)

        prompt = PROMPT_TEMPLATE + text + "\n"
        raw_response = call_ollama(prompt, model)

        try:
            summary = json.loads(raw_response)
        except json.JSONDecodeError:
            summary = {"page": i, "summary": raw_response.strip()}

        summaries.append(summary)

    return summaries

# API models
class Summary(BaseModel):
    page: int
    summary: str

class Document(BaseModel):
    id: int
    pdf_url: str
    model: str
    total_pages: int
    status: str
    created_at: str

class DocumentSummary(BaseModel):
    document: Document
    summaries: List[Summary]

# FastAPI endpoints
@app.get("/summarize", response_model=List[Summary])
async def api_summarize(pdf_url: str = Query(..., description="URL to a PDF"),
                        model: str = Query("qwen2.5vl:7b", description="Ollama model name")):
    """Summarize a PDF and store results in database"""
    resp = requests.get(pdf_url)
    if resp.status_code != 200:
        raise HTTPException(400, f"Could not download PDF: {resp.status_code}")
    summaries = summarize_pdf_bytes_with_db(resp.content, pdf_url, model)
    return summaries

@app.get("/documents", response_model=List[Document])
async def get_all_documents():
    """Get all processed documents"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    documents = cursor.fetchall()
    conn.close()
    
    return [
        Document(
            id=doc["id"],
            pdf_url=doc["pdf_url"],
            model=doc["model"],
            total_pages=doc["total_pages"],
            status=doc["status"],
            created_at=doc["created_at"]
        )
        for doc in documents
    ]

@app.get("/documents/{document_id}", response_model=DocumentSummary)
async def get_document_with_summaries(document_id: int):
    """Get a specific document with its summaries"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get document
    cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
    document = cursor.fetchone()
    
    if not document:
        conn.close()
        raise HTTPException(404, "Document not found")
    
    # Get summaries
    cursor.execute("SELECT page_number, summary FROM summaries WHERE pdf_url = ? ORDER BY page_number", 
                   (document["pdf_url"],))
    summaries = cursor.fetchall()
    conn.close()
    
    return DocumentSummary(
        document=Document(
            id=document["id"],
            pdf_url=document["pdf_url"],
            model=document["model"],
            total_pages=document["total_pages"],
            status=document["status"],
            created_at=document["created_at"]
        ),
        summaries=[Summary(page=s["page_number"], summary=s["summary"]) for s in summaries]
    )

@app.get("/summaries/{pdf_url:path}")
async def get_summaries_by_url(pdf_url: str):
    """Get summaries for a specific PDF URL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT page_number, summary FROM summaries WHERE pdf_url = ? ORDER BY page_number", 
                   (pdf_url,))
    summaries = cursor.fetchall()
    conn.close()
    
    if not summaries:
        raise HTTPException(404, "No summaries found for this PDF URL")
    
    return [{"page": s["page_number"], "summary": s["summary"]} for s in summaries]

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and its summaries"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get document to find PDF URL
    cursor.execute("SELECT pdf_url FROM documents WHERE id = ?", (document_id,))
    document = cursor.fetchone()
    
    if not document:
        conn.close()
        raise HTTPException(404, "Document not found")
    
    # Delete summaries first
    cursor.execute("DELETE FROM summaries WHERE pdf_url = ?", (document["pdf_url"],))
    
    # Delete document
    cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Document and summaries deleted successfully"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PDF Summarization API",
        "endpoints": {
            "GET /": "This endpoint",
            "GET /summarize?pdf_url=<url>&model=<model>": "Summarize a PDF",
            "GET /documents": "Get all processed documents",
            "GET /documents/{id}": "Get document with summaries",
            "GET /summaries/{pdf_url}": "Get summaries by PDF URL",
            "DELETE /documents/{id}": "Delete document and summaries"
        }
    }

# CLI mode
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Summarize a PDF using Ollama")
    parser.add_argument('--pdf', help='Local file path or URL to PDF')
    parser.add_argument('--output', help='Path to save summary JSON')
    parser.add_argument('--model', default='qwen2.5vl:7b', help='Ollama model name')
    parser.add_argument('--serve', action='store_true', help='Run as FastAPI server')
    args = parser.parse_args()

    if args.serve:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    elif args.pdf and args.output:
        if args.pdf.startswith("http"):
            r = requests.get(args.pdf)
            if r.status_code != 200:
                print(f"Error downloading PDF: {r.status_code}")
                exit(1)
            pdf_data = r.content
        else:
            if not os.path.exists(args.pdf):
                print("Local file not found")
                exit(1)
            with open(args.pdf, 'rb') as f:
                pdf_data = f.read()

        result = summarize_pdf_bytes(pdf_data, args.model)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Summaries saved to {args.output}")
    else:
        parser.print_help()