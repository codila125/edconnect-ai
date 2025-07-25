import fitz  # PyMuPDF
import sqlite3
import requests
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io
import os

# Configuration
PDF_PATH = "FinalReport.pdf"
API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5vl:7b"
OUTPUT_DIR = "extracted_images"

# Create output directory for images
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Keywords for manpower planning and hiring
KEYWORDS = [
    'manpower', 'hiring', 'recruitment', 'employee', 'staff', 'workforce',
    'hr', 'human resources', 'talent', 'personnel', 'onboarding',
    'retention', 'training', 'development', 'organization', 'management'
]

# Mathematical content patterns
MATH_PATTERNS = [
    r'\b\d{1,2}-\d{1,2}\b',  # ranges like 4-5
    r'\b\d+\s*years?\b',      # years
    r'\b\d+\s*months?\b',     # months
    r'\b\d+%\b',              # percentages
    r'\$\d+',                 # currency
    r'\b\d+\.\d+\b'           # decimals
]

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

def extract_and_save_images(doc, page_num):
    """Extract images from a PDF page and save them"""
    page = doc[page_num - 1]
    image_list = page.get_images()
    
    extracted_images = []
    
    for i, img in enumerate(image_list):
        # Get the XREF of the image
        xref = img[0]
        
        # Extract the image
        pix = fitz.Pixmap(doc, xref)
        
        # Convert to PIL Image if needed
        if pix.n - pix.alpha < 4:  # GRAY or RGB
            img_data = pix.tobytes("png")
            image_path = f"{OUTPUT_DIR}/page_{page_num}_image_{i+1}.png"
            
            with open(image_path, "wb") as f:
                f.write(img_data)
                
            extracted_images.append({
                'path': image_path,
                'width': pix.width,
                'height': pix.height,
                'index': i+1
            })
            
            print(f"   💾 Saved: {image_path} ({pix.width}x{pix.height})")
        
        pix = None  # Free memory
    
    return extracted_images

def analyze_image_with_ocr(image_path):
    """Analyze image content using OCR"""
    try:
        # Enhanced OCR configuration for better text extraction
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:!?()[]{}+-*/=<>%$@#&_'
        
        # Extract text from image
        image = Image.open(image_path)
        ocr_text = pytesseract.image_to_string(image, config=config).strip()
        
        return ocr_text
    except Exception as e:
        print(f"   ⚠️ OCR Error: {e}")
        return ""

def generate_image_summary(image_info, ocr_text, page_num):
    """Generate summary for image content"""
    
    # Check if OCR text contains relevant keywords
    ocr_lower = ocr_text.lower()
    relevant_keywords = [kw for kw in KEYWORDS if kw in ocr_lower]
    
    # Detect mathematical content in OCR text
    math_content = []
    for pattern in MATH_PATTERNS:
        math_content.extend(re.findall(pattern, ocr_text, re.IGNORECASE))
    
    # Create detailed image analysis
    analysis_parts = []
    
    analysis_parts.append(f"🖼️ IMAGE ANALYSIS - Page {page_num}")
    analysis_parts.append("=" * 50)
    
    # Image metadata
    analysis_parts.append(f"\n📊 IMAGE METADATA:")
    analysis_parts.append(f"• Image file: {os.path.basename(image_info['path'])}")
    analysis_parts.append(f"• Dimensions: {image_info['width']} x {image_info['height']} pixels")
    analysis_parts.append(f"• Page location: Page {page_num}, Image {image_info['index']}")
    
    # OCR Results
    if ocr_text.strip():
        analysis_parts.append(f"\n📝 EXTRACTED TEXT:")
        # Clean and format the OCR text
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        for line in lines[:10]:  # Limit to first 10 lines
            analysis_parts.append(f"• {line}")
        if len(lines) > 10:
            analysis_parts.append(f"• ... and {len(lines)-10} more lines")
    else:
        analysis_parts.append(f"\n📝 EXTRACTED TEXT: No readable text detected")
    
    # Keyword analysis
    if relevant_keywords:
        analysis_parts.append(f"\n🎯 RELEVANT KEYWORDS FOUND:")
        for kw in relevant_keywords:
            analysis_parts.append(f"• {kw}")
    else:
        analysis_parts.append(f"\n🎯 RELEVANT KEYWORDS: None detected")
    
    # Mathematical content
    if math_content:
        analysis_parts.append(f"\n🔢 MATHEMATICAL CONTENT:")
        for math in list(set(math_content)):
            analysis_parts.append(f"• {math}")
    else:
        analysis_parts.append(f"\n🔢 MATHEMATICAL CONTENT: None detected")
    
    # Content analysis
    analysis_parts.append(f"\n💡 CONTENT ANALYSIS:")
    if relevant_keywords and any(kw in ['manpower', 'hiring', 'employee', 'hr'] for kw in relevant_keywords):
        analysis_parts.append("• Image contains HR/manpower related content")
        analysis_parts.append("• Likely shows organizational charts, process flows, or metrics")
    elif math_content:
        analysis_parts.append("• Image contains quantitative data")
        analysis_parts.append("• May show charts, graphs, or statistical information")
    elif ocr_text.strip():
        analysis_parts.append("• Image contains textual information")
        analysis_parts.append("• Could be forms, documents, or informational content")
    else:
        analysis_parts.append("• Image appears to be graphical/visual content")
        analysis_parts.append("• May contain charts, diagrams, or illustrations")
    
    # AI Summary attempt
    if ocr_text.strip():
        try:
            prompt = f"""Analyze this image content extracted from a PDF about manpower planning and hiring.
            
Image contains this text:
{ocr_text}

Please provide insights about:
1. What type of visual content this represents
2. Relevance to manpower planning and hiring
3. Key information or data shown
4. Strategic insights

Focus on HR, recruitment, organizational structure, or workforce management aspects."""

            print(f"   🤖 Generating AI analysis for image...")
            
            response = requests.post(API_URL, json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }, timeout=60)

            if response.ok:
                ai_summary = response.json().get("response", "")
                if ai_summary:
                    analysis_parts.append(f"\n🤖 AI ANALYSIS:")
                    analysis_parts.append(ai_summary)
            else:
                analysis_parts.append(f"\n🤖 AI ANALYSIS: API Error - {response.status_code}")
                
        except Exception as e:
            analysis_parts.append(f"\n🤖 AI ANALYSIS: Error - {str(e)}")
    
    return '\n'.join(analysis_parts), len(relevant_keywords) > 0, len(math_content) > 0

def process_page_with_images(page_num):
    """Process a specific page that contains images"""
    print(f"\n🔍 Processing page {page_num} with images...")
    
    conn, cursor = setup_database()
    doc = fitz.open(PDF_PATH)
    
    # Check if already processed
    cursor.execute("""
        SELECT COUNT(*) FROM summaries 
        WHERE page = ? AND content_type LIKE '%image%'
    """, (page_num,))
    
    existing_count = cursor.fetchone()[0]
    if existing_count > 0:
        print(f"⚠️ Page {page_num} images already processed. Skipping...")
        doc.close()
        conn.close()
        return
    
    # Extract and save images
    extracted_images = extract_and_save_images(doc, page_num)
    
    if not extracted_images:
        print(f"❌ No images could be extracted from page {page_num}")
        doc.close()
        conn.close()
        return
    
    # Process each image
    for img_info in extracted_images:
        print(f"\n📸 Analyzing image {img_info['index']}...")
        
        # OCR analysis
        ocr_text = analyze_image_with_ocr(img_info['path'])
        
        # Generate summary
        summary, has_keywords, has_math = generate_image_summary(img_info, ocr_text, page_num)
        
        # Save to database
        content_type = f"image_{img_info['index']}_analysis"
        
        cursor.execute("""
            INSERT INTO summaries (page, content_type, summary, has_equations, has_images)
            VALUES (?, ?, ?, ?, ?)
        """, (page_num, content_type, summary, has_math, True))
        
        print(f"   ✅ Image {img_info['index']} analysis saved to database")
    
    conn.commit()
    doc.close()
    conn.close()
    
    print(f"✅ Completed processing {len(extracted_images)} images from page {page_num}")

def main():
    """Main function to process all pages with images"""
    print("🚀 Starting Image Analysis for PDF...")
    
    # Pages with images (from our scan)
    pages_with_images = [1, 15, 16]
    
    for page_num in pages_with_images:
        process_page_with_images(page_num)
    
    print(f"\n🎯 Image analysis complete for {len(pages_with_images)} pages!")
    print("💡 Use check_db.py to view the results or export with extraction.py --export")

if __name__ == "__main__":
    main()
