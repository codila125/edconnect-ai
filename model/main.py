from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
import requests, io, json, argparse, os
from PyPDF2 import PdfReader
import easyocr
from datetime import datetime
from typing import List, Optional
import textwrap
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import User, Content, Material
from database import get_db, Base, engine

# FastAPI instance
app = FastAPI()

# Initialize OCR
ocr_reader = easyocr.Reader(['en'], gpu=False)

# Unified prompt for summarization
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

def get_image_from_pdf_page(pdf_bytes: bytes, page_num: int) -> bytes:
    """Convert a PDF page to PNG bytes using PyMuPDF with higher DPI"""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(dpi=300)
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

# PDF summarization logic with database update
async def summarize_pdf_bytes_with_db(pdf_bytes: bytes, pdf_url: str, model: str = "qwen2.5vl:7b", db: AsyncSession = None) -> dict:
    """
    Summarize PDF and update the summary field in contents table for matching PDF URL
    """
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    page_summaries = []
    
    # Process each page
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

        page_summaries.append(f"Page {i}: {page_summary}")

    # Combine all page summaries into one comprehensive summary
    combined_summary = "\n\n".join(page_summaries)
    
    # Update the database - find content with matching PDF URL and update summary
    if db:
        try:
            # First, find the material with the PDF URL
            material_query = select(Material).where(Material.url == pdf_url)
            result = await db.execute(material_query)
            material = result.scalar_one_or_none()
            
            if material:
                # Update all contents that reference this material
                update_query = update(Content).where(
                    Content.material_id == material.id
                ).values(summary=combined_summary)
                
                await db.execute(update_query)
                await db.commit()
                print(f"[Info] Updated summary for material: {material.name}")
            else:
                print(f"[Warning] No material found with URL: {pdf_url}")
                
        except Exception as e:
            print(f"[Database Error] {str(e)}")
            await db.rollback()
    
    return {
        "pdf_url": pdf_url,
        "total_pages": len(pdf.pages),
        "summary": combined_summary,
        "model_used": model,
        "processed_at": datetime.utcnow().isoformat()
    }

# Updated function for standalone use (without database)
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
class SummaryResponse(BaseModel):
    pdf_url: str
    total_pages: int
    summary: str
    model_used: str
    processed_at: str

class ContentInfo(BaseModel):
    id: str
    title: str
    summary: Optional[str]
    material_url: str

# FastAPI endpoints
@app.get("/summarize", response_model=SummaryResponse)
async def api_summarize(
    pdf_url: str = Query(..., description="URL to a PDF"),
    model: str = Query("qwen2.5vl:7b", description="Ollama model name"),
    db: AsyncSession = Depends(get_db)
):
    """Summarize a PDF and update the summary field in contents table"""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(pdf_url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(
            400,
            f"Failed to fetch PDF from URL: {pdf_url}, "
            f"Status Code: {resp.status_code}, Content: {resp.content[:100]}"
        )

    result = await summarize_pdf_bytes_with_db(resp.content, pdf_url, model, db)
    return result

@app.get("/contents", response_model=List[ContentInfo])
async def get_all_contents(db: AsyncSession = Depends(get_db)):
    """Get all contents with their material URLs"""
    query = select(Content, Material).join(Material, Content.material_id == Material.id)
    result = await db.execute(query)
    contents = result.all()
    
    return [
        ContentInfo(
            id=content.Content.id,
            title=content.Content.title,
            summary=content.Content.summary,
            material_url=content.Material.url
        )
        for content in contents
    ]

@app.get("/contents/{content_id}", response_model=ContentInfo)
async def get_content_by_id(content_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific content with its material URL"""
    query = select(Content, Material).join(Material, Content.material_id == Material.id).where(Content.id == content_id)
    result = await db.execute(query)
    content = result.first()
    
    if not content:
        raise HTTPException(404, "Content not found")
    
    return ContentInfo(
        id=content.Content.id,
        title=content.Content.title,
        summary=content.Content.summary,
        material_url=content.Material.url
    )

@app.get("/contents/by-url/{pdf_url:path}")
async def get_contents_by_pdf_url(pdf_url: str, db: AsyncSession = Depends(get_db)):
    """Get all contents that reference a specific PDF URL"""
    query = select(Content, Material).join(Material, Content.material_id == Material.id).where(Material.url == pdf_url)
    result = await db.execute(query)
    contents = result.all()
    
    if not contents:
        raise HTTPException(404, "No contents found for this PDF URL")
    
    return [
        ContentInfo(
            id=content.Content.id,
            title=content.Content.title,
            summary=content.Content.summary,
            material_url=content.Material.url
        )
        for content in contents
    ]

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PDF Summarization API with Neon PostgreSQL",
        "endpoints": {
            "GET /": "This endpoint",
            "GET /summarize?pdf_url=<url>&model=<model>": "Summarize a PDF and update database",
            "GET /contents": "Get all contents with material URLs",
            "GET /contents/{id}": "Get content by ID",
            "GET /contents/by-url/{pdf_url}": "Get contents by PDF URL"
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