import fitz  # PyMuPDF
import sqlite3
import requests
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io
import os

# Configuration for DS3.pdf
PDF_PATH = "DS3.pdf"
API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5vl:7b"
OUTPUT_DIR = "ds3_extracted_images"

# Create output directory for images
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_database():
    """Set up SQLite database for storing summaries"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page INTEGER,
            content_type TEXT,
            summary TEXT,
            has_equations BOOLEAN DEFAULT 0,
            has_images BOOLEAN DEFAULT 0
        )
    """)
    
    # Add columns if they don't exist
    try:
        cursor.execute("ALTER TABLE summaries ADD COLUMN has_equations BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE summaries ADD COLUMN has_images BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    return conn, cursor

def extract_and_save_image(doc, page_num):
    """Extract the main image from a DS3 PDF page"""
    page = doc[page_num - 1]
    image_list = page.get_images()
    
    if not image_list:
        return None
    
    # Get the first (and typically only) image
    img = image_list[0]
    xref = img[0]
    
    # Extract the image
    pix = fitz.Pixmap(doc, xref)
    
    # Convert to PNG and save
    if pix.n - pix.alpha < 4:  # GRAY or RGB
        img_data = pix.tobytes("png")
        image_path = f"{OUTPUT_DIR}/ds3_page_{page_num}.png"
        
        with open(image_path, "wb") as f:
            f.write(img_data)
            
        image_info = {
            'path': image_path,
            'width': pix.width,
            'height': pix.height,
            'page': page_num
        }
        
        print(f"   💾 Saved: {image_path} ({pix.width}x{pix.height})")
        pix = None  # Free memory
        return image_info
    
    pix = None
    return None

def analyze_ds3_image_with_ocr(image_path):
    """Analyze DS3 image content using OCR with enhanced configuration"""
    try:
        # Enhanced OCR configuration for documents/charts
        config = r'--oem 3 --psm 3'  # PSM 3 is better for general documents
        
        # Load and potentially resize image for better OCR
        image = Image.open(image_path)
        
        # If image is very large, resize for better OCR performance
        if image.width > 2000 or image.height > 2000:
            # Calculate new size maintaining aspect ratio
            ratio = min(2000/image.width, 2000/image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            print(f"   📏 Resized image to {new_size} for better OCR")
        
        # Extract text from image
        ocr_text = pytesseract.image_to_string(image, config=config).strip()
        
        return ocr_text
    except Exception as e:
        print(f"   ⚠️ OCR Error: {e}")
        return ""

def generate_ds3_summary(image_info, ocr_text, page_num):
    """Generate comprehensive summary for DS3 image content"""
    
    # Analyze OCR text for content patterns
    ocr_lower = ocr_text.lower()
    
    # Detect various content types
    has_tables = any(indicator in ocr_lower for indicator in ['table', 'row', 'column', '|', 'total', 'sum'])
    has_charts = any(indicator in ocr_lower for indicator in ['chart', 'graph', 'axis', 'legend', 'data'])
    has_forms = any(indicator in ocr_lower for indicator in ['form', 'name:', 'date:', 'signature', 'field'])
    has_equations = bool(re.search(r'[=+\-*/]|\d+\.\d+|\d+%', ocr_text))
    has_dates = bool(re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}', ocr_text))
    has_numbers = bool(re.search(r'\b\d+\b', ocr_text))
    
    # Create analysis
    analysis_parts = []
    
    analysis_parts.append(f"📊 DS3 IMAGE ANALYSIS - Page {page_num}")
    analysis_parts.append("=" * 60)
    
    # Image metadata
    analysis_parts.append(f"\n🖼️ IMAGE PROPERTIES:")
    analysis_parts.append(f"• Source: DS3.pdf, Page {page_num}")
    analysis_parts.append(f"• Dimensions: {image_info['width']} x {image_info['height']} pixels")
    analysis_parts.append(f"• File: {os.path.basename(image_info['path'])}")
    analysis_parts.append(f"• Resolution: High-resolution document image")
    
    # Content type detection
    analysis_parts.append(f"\n🔍 CONTENT TYPE ANALYSIS:")
    content_types = []
    if has_tables: content_types.append("📋 Tabular data")
    if has_charts: content_types.append("📈 Charts/Graphs")
    if has_forms: content_types.append("📝 Forms/Documents")
    if has_equations: content_types.append("🔢 Mathematical content")
    if has_dates: content_types.append("📅 Date information")
    if has_numbers: content_types.append("🔢 Numerical data")
    
    if content_types:
        for ct in content_types:
            analysis_parts.append(f"• {ct}")
    else:
        analysis_parts.append("• 🖼️ Visual/Graphical content")
    
    # OCR Results
    if ocr_text.strip():
        analysis_parts.append(f"\n📝 EXTRACTED TEXT CONTENT:")
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        
        # Show first 15 lines of meaningful content
        shown_lines = 0
        for line in lines:
            if shown_lines >= 15:
                break
            if len(line) > 2:  # Skip very short lines
                analysis_parts.append(f"• {line}")
                shown_lines += 1
        
        if len(lines) > 15:
            analysis_parts.append(f"• ... and {len(lines)-15} more lines of text")
        
        analysis_parts.append(f"\n📊 TEXT STATISTICS:")
        analysis_parts.append(f"• Total lines extracted: {len(lines)}")
        analysis_parts.append(f"• Total characters: {len(ocr_text)}")
        analysis_parts.append(f"• Contains numbers: {'Yes' if has_numbers else 'No'}")
        analysis_parts.append(f"• Contains dates: {'Yes' if has_dates else 'No'}")
        analysis_parts.append(f"• Contains equations: {'Yes' if has_equations else 'No'}")
    else:
        analysis_parts.append(f"\n📝 EXTRACTED TEXT: No readable text detected")
        analysis_parts.append("• This may be a purely visual image (diagram, photo, etc.)")
    
    # Try AI analysis
    if ocr_text.strip():
        try:
            prompt = f"""Analyze this document image content from DS3.pdf page {page_num}.

The image contains this extracted text:
{ocr_text[:2000]}

Please provide:
1. Document type identification (form, chart, table, diagram, etc.)
2. Main purpose and content summary
3. Key data points or information
4. Business/academic context if identifiable
5. Any notable patterns or insights

Be specific about what type of document this appears to be and what information it contains."""

            print(f"   🤖 Generating AI analysis...")
            
            response = requests.post(API_URL, json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }, timeout=90)

            if response.ok:
                ai_summary = response.json().get("response", "")
                if ai_summary:
                    analysis_parts.append(f"\n🤖 INTELLIGENT ANALYSIS:")
                    analysis_parts.append(ai_summary)
                    print(f"   ✅ AI analysis completed")
            else:
                analysis_parts.append(f"\n🤖 AI ANALYSIS: API Error - {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ AI analysis failed: {e}")
            analysis_parts.append(f"\n🤖 AI ANALYSIS: Failed - {str(e)}")
    
    # Manual insights based on content patterns
    analysis_parts.append(f"\n💡 DOCUMENT INSIGHTS:")
    if has_tables and has_numbers:
        analysis_parts.append("• Appears to be a data table or spreadsheet")
        analysis_parts.append("• Contains structured numerical information")
    if has_forms:
        analysis_parts.append("• Document appears to be a form or application")
    if has_charts:
        analysis_parts.append("• Contains visual data representation")
    if has_dates:
        analysis_parts.append("• Time-series or dated information present")
    if len(ocr_text) > 1000:
        analysis_parts.append("• Rich text content - likely a detailed document")
    elif len(ocr_text) < 100 and has_numbers:
        analysis_parts.append("• Minimal text - likely a chart, diagram, or form")
    
    return '\n'.join(analysis_parts), has_equations, True

def process_ds3_page(page_num):
    """Process a specific page from DS3.pdf"""
    print(f"\n🔍 Processing DS3.pdf page {page_num}...")
    
    conn, cursor = setup_database()
    doc = fitz.open(PDF_PATH)
    
    # Check if already processed
    cursor.execute("""
        SELECT COUNT(*) FROM summaries 
        WHERE page = ? AND content_type = ?
    """, (page_num, f"ds3_page_{page_num}"))
    
    existing_count = cursor.fetchone()[0]
    if existing_count > 0:
        print(f"⚠️ DS3 page {page_num} already processed. Skipping...")
        doc.close()
        conn.close()
        return
    
    # Extract and save image
    image_info = extract_and_save_image(doc, page_num)
    
    if not image_info:
        print(f"❌ Could not extract image from DS3 page {page_num}")
        doc.close()
        conn.close()
        return
    
    # OCR analysis
    print(f"   🔤 Running OCR analysis...")
    ocr_text = analyze_ds3_image_with_ocr(image_info['path'])
    
    # Generate comprehensive summary
    summary, has_math, has_images = generate_ds3_summary(image_info, ocr_text, page_num)
    
    # Save to database
    content_type = f"ds3_page_{page_num}"
    
    cursor.execute("""
        INSERT INTO summaries (page, content_type, summary, has_equations, has_images)
        VALUES (?, ?, ?, ?, ?)
    """, (page_num, content_type, summary, has_math, has_images))
    
    conn.commit()
    doc.close()
    conn.close()
    
    print(f"   ✅ DS3 page {page_num} analysis saved to database")

def main():
    """Process specific pages or all pages of DS3.pdf"""
    print("🚀 Starting DS3.pdf Image Analysis...")
    
    # Process all 8 pages
    for page_num in range(1, 9):
        process_ds3_page(page_num)
    
    print(f"\n🎯 DS3.pdf analysis complete!")
    print("💡 Use check_db.py to view results or export with extraction.py --export")

if __name__ == "__main__":
    main()
