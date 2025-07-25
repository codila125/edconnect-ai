from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import requests, io, json, argparse, os
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import easyocr

# Initialize OCR
ocr_reader = easyocr.Reader(['en'], gpu=False)

# FastAPI instance
app = FastAPI()

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

# PDF summarization logic
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

# API model
class Summary(BaseModel):
    page: int
    summary: str

# FastAPI endpoint
@app.get("/summarize", response_model=list[Summary])
async def api_summarize(pdf_url: str = Query(..., description="URL to a PDF"),
                        model: str = Query("qwen2.5vl:7b", description="Ollama model name")):
    resp = requests.get(pdf_url)
    if resp.status_code != 200:
        raise HTTPException(400, f"Could not download PDF: {resp.status_code}")
    summaries = summarize_pdf_bytes(resp.content, model)
    return summaries

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
        uvicorn.run("main:app", host="0.0.0.0", port=8000)
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
        