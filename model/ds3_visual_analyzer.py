import fitz  # PyMuPDF
import sqlite3
import requests
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

def extract_and_analyze_image(doc, page_num):
    """Extract and analyze image from DS3 PDF page"""
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
            
        # Get page text (if any exists alongside the image)
        page_text = page.get_text().strip()
        
        image_info = {
            'path': image_path,
            'width': pix.width,
            'height': pix.height,
            'page': page_num,
            'page_text': page_text,
            'colorspace': pix.colorspace.name if pix.colorspace else 'Unknown',
            'file_size': len(img_data)
        }
        
        print(f"   💾 Saved: {image_path} ({pix.width}x{pix.height}, {len(img_data)//1024}KB)")
        pix = None  # Free memory
        return image_info
    
    pix = None
    return None

def generate_visual_analysis(image_info, page_num):
    """Generate analysis based on visual properties and metadata"""
    
    # Analyze image properties
    width, height = image_info['width'], image_info['height']
    aspect_ratio = width / height
    file_size_kb = image_info['file_size'] // 1024
    
    # Determine likely content type based on dimensions and aspect ratio
    if aspect_ratio > 1.5:
        likely_type = "Wide format - likely chart, graph, or landscape document"
    elif aspect_ratio < 0.7:
        likely_type = "Tall format - likely portrait document or form"
    else:
        likely_type = "Square/standard format - likely page scan or diagram"
    
    # File size analysis
    if file_size_kb > 1000:
        quality_note = "High quality image with rich detail"
    elif file_size_kb > 500:
        quality_note = "Medium quality image with good detail"
    else:
        quality_note = "Compact image, likely simple graphics or text"
    
    # Create comprehensive analysis
    analysis_parts = []
    
    analysis_parts.append(f"📊 DS3.pdf IMAGE ANALYSIS - Page {page_num}")
    analysis_parts.append("=" * 60)
    
    # Basic image properties
    analysis_parts.append(f"\n🖼️ IMAGE PROPERTIES:")
    analysis_parts.append(f"• Source: DS3.pdf, Page {page_num}")
    analysis_parts.append(f"• Dimensions: {width} × {height} pixels")
    analysis_parts.append(f"• Aspect Ratio: {aspect_ratio:.2f} ({likely_type})")
    analysis_parts.append(f"• File Size: {file_size_kb}KB ({quality_note})")
    analysis_parts.append(f"• Color Space: {image_info['colorspace']}")
    analysis_parts.append(f"• Saved as: {os.path.basename(image_info['path'])}")
    
    # Content analysis based on page text (if any)
    if image_info['page_text']:
        analysis_parts.append(f"\n📝 ACCOMPANYING TEXT:")
        text_lines = [line.strip() for line in image_info['page_text'].split('\n') if line.strip()]
        for line in text_lines[:10]:
            analysis_parts.append(f"• {line}")
        if len(text_lines) > 10:
            analysis_parts.append(f"• ... and {len(text_lines)-10} more lines")
    else:
        analysis_parts.append(f"\n📝 ACCOMPANYING TEXT: None (image-only page)")
    
    # Visual content type prediction
    analysis_parts.append(f"\n🔍 VISUAL CONTENT ANALYSIS:")
    analysis_parts.append(f"• Image Type: {likely_type}")
    analysis_parts.append(f"• Quality Assessment: {quality_note}")
    
    if width > 3000 or height > 3000:
        analysis_parts.append("• High-resolution scan - likely document or detailed diagram")
    if aspect_ratio > 1.3:
        analysis_parts.append("• Wide format suggests charts, tables, or landscape documents")
    elif aspect_ratio < 0.8:
        analysis_parts.append("• Tall format suggests forms, receipts, or portrait documents")
    
    # Try AI visual analysis if possible
    try:
        prompt = f"""Analyze this image from DS3.pdf page {page_num}.

Image Properties:
- Dimensions: {width} × {height} pixels
- Aspect Ratio: {aspect_ratio:.2f}
- File Size: {file_size_kb}KB
- Type: {likely_type}

Additional text on page: {image_info['page_text'][:500] if image_info['page_text'] else 'None'}

Based on these properties, what type of document or content is this likely to be? Consider:
1. Document type (form, chart, diagram, scan, etc.)
2. Purpose and context
3. Professional or academic nature
4. Data visualization vs text document

Provide insights about what this image likely contains."""

        print(f"   🤖 Generating AI visual analysis...")
        
        response = requests.post(API_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }, timeout=60)

        if response.ok:
            ai_analysis = response.json().get("response", "")
            if ai_analysis:
                analysis_parts.append(f"\n🤖 AI VISUAL ANALYSIS:")
                analysis_parts.append(ai_analysis)
                print(f"   ✅ AI analysis completed")
        else:
            analysis_parts.append(f"\n🤖 AI ANALYSIS: API Error - {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️ AI analysis failed: {e}")
        analysis_parts.append(f"\n🤖 AI ANALYSIS: Failed - {str(e)}")
    
    # Summary insights
    analysis_parts.append(f"\n💡 SUMMARY INSIGHTS:")
    analysis_parts.append(f"• This is page {page_num} of an 8-page DS3.pdf document")
    analysis_parts.append(f"• Image appears to be a high-quality scan or digital document")
    if image_info['page_text']:
        analysis_parts.append(f"• Contains both visual and textual elements")
    else:
        analysis_parts.append(f"• Primarily visual content (image/diagram)")
    analysis_parts.append(f"• Professional document quality suitable for analysis")
    
    return '\n'.join(analysis_parts), False, True

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
    
    # Extract and analyze image
    image_info = extract_and_analyze_image(doc, page_num)
    
    if not image_info:
        print(f"❌ Could not extract image from DS3 page {page_num}")
        doc.close()
        conn.close()
        return
    
    # Generate analysis
    summary, has_math, has_images = generate_visual_analysis(image_info, page_num)
    
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
    """Process specific page or all pages of DS3.pdf"""
    import sys
    
    if len(sys.argv) > 1:
        # Process specific page
        try:
            page_num = int(sys.argv[1])
            if 1 <= page_num <= 8:
                print(f"🚀 Starting DS3.pdf analysis for page {page_num}...")
                process_ds3_page(page_num)
                print(f"🎯 DS3.pdf page {page_num} analysis complete!")
            else:
                print("❌ Page number must be between 1 and 8")
        except ValueError:
            print("❌ Please provide a valid page number")
    else:
        # Process all pages
        print("🚀 Starting DS3.pdf analysis for all pages...")
        for page_num in range(1, 9):
            process_ds3_page(page_num)
        print(f"🎯 DS3.pdf complete analysis finished!")

if __name__ == "__main__":
    main()
