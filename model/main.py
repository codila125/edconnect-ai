from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
import requests, io, json, argparse, os
from PyPDF2 import PdfReader
import easyocr
import sqlite3
from datetime import datetime
from typing import List, Optional
import textwrap  # Already present, keep it
from typing import Tuple  # Add this import

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
import textwrap

SUMMARY_SENTENCE_MIN = 3
SUMMARY_SENTENCE_MAX = 6
SUMMARY_WORDS = 150

PROMPT_TEMPLATE = textwrap.dedent("""\
You are an expert summarizer for scientific and technical documents. Your primary goal is to provide concise, accurate, and contextually rich summaries. 
You must adhere strictly to the information provided in the input text and image descriptions, without introducing any external knowledge or fabricating details.
For tables: Report key rows/columns exactly as shown, don't aggregate unless specified

**Task:** Summarize the following document.

**Input Document (including text, equations, and image descriptions):**
<START_DOCUMENT>
[Insert the pre-processed document content here. This includes:
1. All textual content from the document (from text-extraction or OCR).
2. LaTeX representations of all equations.
3. Concise, factual descriptions of each relevant image.
]
<END_DOCUMENT>

**Specific Instructions for Summarization:**

1. **Conciseness and Length:** Provide a summary of approximately {SUMMARY_SENTENCE_MIN} to {SUMMARY_SENTENCE_MAX} sentences, or about {SUMMARY_WORDS} words. Focus on the core findings, methodologies, and significant conclusions.

2. **Factual Accuracy and No Hallucination:**
   * **Important:** Do NOT invent any information, details, or theories not explicitly stated in the provided `Input Document`.
   * If a concept, detail, or value is not present in the document, state that the information is not provided or omit it. Do not guess.
   * Every statement in the summary must be directly supported by the `Input Document`.

3. **Image Summarization:**
   * Pay special attention to image descriptions as they contain critical information.
   * For charts and graphs, report the key data points and trends exactly as described.
   * For diagrams, describe the components and relationships exactly as presented.
   * For pie charts, report the exact percentages and categories mentioned.

4. **Language and Tone:** Use clear, formal, and objective language. Avoid colloquialisms or subjective interpretations.

**Example:**
Input: [Image 1: A pie chart showing budget distribution: Department A: 45%, Department B: 25%, Department C: 15%, Department D: 10%, Department E: 5%]
Summary: The budget distribution pie chart shows Department A receives the largest share at 45%, followed by Department B (25%), Department C (15%), Department D (10%), and Department E (5%).
"SPECIAL CASES:\n"
"1. If page is blank: 'This page appears intentionally left blank'\n"
"2. For graphical-only pages: 'This page contains diagrams/charts without accompanying text'\n"
"3. For processing errors: 'Could not process this page due to technical limitations'\n"                                  

**Please provide the summary now.**
""")


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
            print(f"[Ollama Error] Status: {res.status_code} | Body: {res.text}")
            return f"[Error {res.status_code}] {res.text}"
    except Exception as e:
        print(f"[Ollama Exception] {str(e)}")
        return f"[Exception] {str(e)}"

# Initialize OCR
ocr_reader = easyocr.Reader(['en'], gpu=False)

def get_image_from_pdf_page(pdf_bytes: bytes, page_num: int) -> bytes:
    """Convert a PDF page to PNG bytes using PyMuPDF with higher DPI"""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(dpi=300)  # Increased from 200 to 300 DPI
        return pix.tobytes("png")
    except ImportError:
        raise RuntimeError("PyMuPDF (fitz) is not installed. Please install it with 'pip install PyMuPDF'")
    except Exception as e:
        raise RuntimeError(f"PyMuPDF error: {str(e)}")
    
def extract_text_with_ocr(img_bytes: bytes) -> Tuple[str, list]:
    """Enhanced OCR extraction with spatial context"""
    results = ocr_reader.readtext(img_bytes, detail=1)
    ocr_text = []
    clean_text = []
    
    for (bbox, text, prob) in results:
        if prob > 0.4:  # Confidence threshold
            position = f"[{int(bbox[0][0])},{int(bbox[0][1])}]"
            ocr_text.append(f"{position} {text}")
            clean_text.append(text)
    
    return "\n".join(ocr_text), clean_text

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
        cursor.execute("SELECT page_number, summary FROM summaries WHERE pdf_url = ? ORDER BY page_number", (pdf_url,))
        existing_summaries = cursor.fetchall()
        conn.close()
        return [{"page": row["page_number"], "summary": row["summary"]} for row in existing_summaries]

    # Process new PDF - FIXED INDENTATION HERE
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        
        if len(text.strip()) < 50:  # Threshold for OCR
            print(f"[Info] Page {i} has insufficient text, using enhanced OCR...")
            try:
                img_bytes = get_image_from_pdf_page(pdf_bytes, i)
                ocr_output, clean_text = extract_text_with_ocr(img_bytes)
            
                if not clean_text:  # If OCR got nothing
                    if len(text.strip()) > 0:  # If original had some text
                        text = f"TEXT CONTENT PAGE {i}:\n{text}"
                    else:
                        # Special handling for truly empty pages
                        text = f"GRAPHICAL CONTENT PAGE {i}:\n[Contains non-text elements only]"
                else:
                    text = f"IMAGE CONTENT PAGE {i}:\n{ocr_output}"
                
            except Exception as e:
                print(f"[OCR Error] Page {i}: {str(e)}")
                text = f"PROCESSING ERROR PAGE {i}:\n{str(e)}"
        else:
            text = f"TEXT CONTENT PAGE {i}:\n{text}"

        prompt = PROMPT_TEMPLATE + text + "\n"
        raw_response = call_ollama(prompt, model)
        page_summary = raw_response.strip()

        # Verify image content was properly summarized
        if "IMAGE CONTENT" in text:
            if not any(char.isdigit() for char in page_summary):
                page_summary = "[WARNING: Potential missing numerical data] " + page_summary

        # Handle special cases
        if "PROCESSING ERROR" in text or "GRAPHICAL CONTENT" in text:
            page_summary = f"Note: This page contains non-text content. {page_summary}"
        elif not page_summary.strip():
            page_summary = "This page appears to be intentionally left blank"

        summary = {"page": i, "summary": page_summary}
        summaries.append(summary)

        # Only insert if this page hasn't been summarized yet
        cursor.execute(
            "SELECT 1 FROM summaries WHERE pdf_url = ? AND page_number = ?",
            (pdf_url, i)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO summaries (pdf_url, model, page_number, summary) VALUES (?, ?, ?, ?)",
                (pdf_url, model, i, page_summary)
            )

    # Store document record
    cursor.execute(
        "INSERT INTO documents (pdf_url, model, total_pages) VALUES (?, ?, ?)",
        (pdf_url, model, len(pdf.pages))
    )
    conn.commit()
    conn.close()
    return summaries

# Updated function using PyMuPDF for OCR
def summarize_pdf_bytes(pdf_bytes: bytes, model: str = "qwen2.5vl:7b") -> list[dict]:
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    summaries = []

    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        
        if len(text.strip()) < 50:
            print(f"[Info] Page {i} has insufficient text, using enhanced OCR...")
            try:
                img_bytes = get_image_from_pdf_page(pdf_bytes, i)
                ocr_output, clean_text = extract_text_with_ocr(img_bytes)
                text = f"IMAGE CONTENT PAGE {i}:\n{ocr_output}"
            except Exception as e:
                print(f"[OCR Error] Page {i}: {str(e)}")
                text = f"[OCR Error] {str(e)}"
        else:
            text = f"TEXT CONTENT PAGE {i}:\n{text}"

        prompt = PROMPT_TEMPLATE + text + "\n"
        raw_response = call_ollama(prompt, model)
        page_summary = raw_response.strip()

        # Add this before storing the summary
        if "PROCESSING ERROR" in text or "GRAPHICAL CONTENT" in text:
            page_summary = f"Note: This page contains non-text content. {page_summary}"
        elif not page_summary.strip():
            page_summary = "This page appears to be intentionally left blank"

        summaries.append({"page": i, "summary": page_summary})

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
    headers = {"User-Agent": "Mozilla/5.0"}  # some servers block non-browser agents
    resp = requests.get(pdf_url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(
        400,
        f"Failed to fetch PDF from URL: {pdf_url}, "
        f"Status Code: {resp.status_code}, Content: {resp.content[:100]}"
    )

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