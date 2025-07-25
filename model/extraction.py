import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
import sqlite3
import requests
import re

PDF_PATH = "FinalReport.pdf"
MODEL_NAME = "qwen2.5vl:7b"
TARGET_PAGE = 12
KEYWORDS = ["manpower planning", "hiring", "recruitment", "staffing", "workforce", "personnel", "human resources", "hr"]
API_URL = "http://localhost:11434/api/generate"

MATH_PATTERNS = [
    r'[=≠<>≤≥±∞∑∏∫∂√π∆∇]',
    r'\d+\s*[+\-*/÷×]\s*\d+',
    r'[a-zA-Z]\s*[=]\s*\d+',
    r'\b\d+%\b',
    r'\$\d+[\d,]*\.?\d*',
    r'\d+\s*(years?|months?|days?)',
    r'\d+\s*(employees?|staff|people)'
]

def setup_database():
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page INTEGER,
            content_type TEXT,
            summary TEXT,
            has_equations BOOLEAN DEFAULT 0,
            has_images BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    return conn, cursor

def clean_duplicates():
    """Remove duplicate entries from the database"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    # Find duplicates
    cursor.execute("""
        SELECT page, content_type, COUNT(*) as count
        FROM summaries 
        WHERE content_type LIKE '%manpower_hiring%'
        GROUP BY page, content_type 
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"🧹 Found {len(duplicates)} duplicate groups. Cleaning up...")
        
        for page, content_type, count in duplicates:
            # Keep only the most recent entry (highest ID)
            cursor.execute("""
                DELETE FROM summaries 
                WHERE page = ? AND content_type = ? 
                AND id NOT IN (
                    SELECT id FROM summaries 
                    WHERE page = ? AND content_type = ?
                    ORDER BY id DESC LIMIT 1
                )
            """, (page, content_type, page, content_type))
            print(f"  ✅ Removed {count-1} duplicates for page {page}")
        
        conn.commit()
        print("🧹 Cleanup completed")
    else:
        print("✅ No duplicates found")
    
    conn.close()

def detect_mathematical_content(text):
    math_matches = []
    for pattern in MATH_PATTERNS:
        math_matches.extend(re.findall(pattern, text, re.IGNORECASE))
    return list(set(math_matches))

def extract_page_content(doc, page_num):
    page = doc[page_num - 1]
    text = page.get_text().strip()
    image_list = page.get_images()
    has_images = bool(image_list)
    ocr_text = ""

    if len(text) < 50:
        images = convert_from_path(PDF_PATH, first_page=page_num, last_page=page_num, dpi=200)
        if images:
            config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:!?()[]{}+-*/=<>%$@#&_'
            ocr_text = pytesseract.image_to_string(images[0], config=config).strip()
            content_type = "ocr"
            final_text = ocr_text
        else:
            return "", "none", False, False, []
    else:
        content_type = "typed"
        final_text = text

    math_content = detect_mathematical_content(final_text)
    has_math = len(math_content) > 0

    return final_text, content_type, has_images, has_math, math_content

def filter_relevant_lines(content, keywords, math_content):
    lines = content.split('\n')
    relevant = []
    for i, line in enumerate(lines):
        line_lower = line.lower()
        has_keywords = any(keyword in line_lower for keyword in keywords)
        has_math = any(math in line for math in math_content)
        if has_keywords or has_math:
            context_range = 3 if has_math else 2
            start = max(0, i - context_range)
            end = min(len(lines), i + context_range + 1)
            relevant.extend(lines[start:end])
    return list(dict.fromkeys(line for line in relevant if line.strip()))

def generate_summary(content, keywords, math_content, has_images, is_filtered=True):
    context_parts = []
    if math_content:
        context_parts.append(f"mathematical formulas: {', '.join(math_content[:5])}")
    if has_images:
        context_parts.append("visual elements")

    context_str = " and ".join(context_parts) if context_parts else "textual information"

    if is_filtered:
        prompt = f"""Analyze the following content focusing on Manpower Planning and Hiring.
Content contains {context_str}.
Provide a summary including:
- Workforce planning and recruitment
- Relevant calculations
- Visual element interpretations

Content:
{content}"""
    else:
        prompt = f"""Extract information related to Manpower Planning and Hiring.
Content includes {context_str}.

Focus areas:
- Strategies and processes
- Calculations or projections
- Visual data interpretations

Content:
{content}"""

    try:
        response = requests.post(API_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }, timeout=30)

        if response.ok:
            return response.json().get("response", "")
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Summary generation failed: {e}")

def main():
    conn, cursor = setup_database()
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)

    print(f"📄 PDF has {total_pages} pages")

    if TARGET_PAGE > total_pages:
        print(f"❌ Page {TARGET_PAGE} out of range (PDF has {total_pages} pages)")
        return

    print(f"🔍 Processing page {TARGET_PAGE}...")
    content, content_type, has_images, has_math, math_content = extract_page_content(doc, TARGET_PAGE)
    
    if not content:
        print("❌ No content found")
        return

    print(f"📝 Content type: {content_type}")
    print(f"🖼️ Has images: {has_images}")
    print(f"🔢 Has mathematical content: {has_math}")
    if math_content:
        print(f"🧮 Math elements: {', '.join(math_content[:5])}")

    # Check if this page already exists to avoid duplicates
    cursor.execute("""
        SELECT COUNT(*) FROM summaries 
        WHERE page = ? AND content_type = ?
    """, (TARGET_PAGE, f"{content_type}_manpower_hiring"))
    
    existing_count = cursor.fetchone()[0]
    if existing_count > 0:
        print(f"⚠️ Page {TARGET_PAGE} already processed. Skipping to avoid duplicates.")
        print("🗑️ To reprocess, delete existing entries first.")
    else:
        filtered_lines = filter_relevant_lines(content, KEYWORDS, math_content)
        
        if filtered_lines:
            filtered_content = '\n'.join(filtered_lines)
            print(f"✅ Found {len(filtered_lines)} relevant lines")
            
            try:
                print("🤖 Generating AI summary...")
                summary = generate_summary(filtered_content, KEYWORDS, math_content, has_images, True)
                print("✅ AI summary generated")
            except Exception as e:
                print(f"⚠️ API Error: {e}")
                # Create a more comprehensive manual summary
                summary = f"""MANUAL SUMMARY - Manpower Planning & Hiring Analysis

📊 OVERVIEW:
- Found {len(filtered_lines)} relevant lines on page {TARGET_PAGE}
- Content type: {content_type}
- Mathematical elements: {', '.join(math_content) if math_content else 'None'}
- Contains images: {'Yes' if has_images else 'No'}

📝 CONTENT ANALYSIS:
{filtered_content}

🔍 KEY INSIGHTS:
- Document contains manpower planning and hiring information
- Mathematical/temporal references detected: {', '.join(math_content) if math_content else 'None'}
- Content appears to be from a business or HR planning document
"""
        else:
            print("⚠️ No specific keywords found, analyzing full content...")
            try:
                summary = generate_summary(content, KEYWORDS, math_content, has_images, False)
                print("✅ Full content analysis completed")
            except Exception as e:
                print(f"⚠️ API Error: {e}")
                summary = f"""MANUAL SUMMARY - Full Page Analysis

📊 OVERVIEW:
- Analyzed full page {TARGET_PAGE} content
- Content type: {content_type}
- Mathematical elements: {', '.join(math_content) if math_content else 'None'}
- Contains images: {'Yes' if has_images else 'No'}

📝 FULL CONTENT:
{content[:1000]}{'...' if len(content) > 1000 else ''}

🔍 NOTE: No specific manpower planning keywords detected, but mathematical content suggests potential workforce-related data.
"""

        # Insert new summary
        cursor.execute("""
            INSERT INTO summaries (page, content_type, summary, has_equations, has_images)
            VALUES (?, ?, ?, ?, ?)
        """, (TARGET_PAGE, f"{content_type}_manpower_hiring", summary, has_math, has_images))
        conn.commit()
        print("✅ Summary saved to database")

    doc.close()

    # Display all summaries
    print("\n" + "="*80)
    print("🎯 MANPOWER PLANNING & HIRING ANALYSIS RESULTS")
    print("="*80)

    cursor.execute("""
        SELECT page, content_type, summary, has_equations, has_images
        FROM summaries
        WHERE content_type LIKE '%manpower_hiring%'
        ORDER BY page
    """)
    rows = cursor.fetchall()
    
    if rows:
        for i, (page, ctype, summary, eq, img) in enumerate(rows, 1):
            indicators = []
            if eq:
                indicators.append("🔢 Math")
            if img:
                indicators.append("🖼️ Images")
            if not indicators:
                indicators.append("📝 Text Only")
            
            status = " | ".join(indicators)
            
            print(f"\n📄 Entry {i} - Page {page}")
            print(f"📊 Type: {ctype}")
            print(f"🏷️ Content: {status}")
            print("-" * 60)
            print(summary)
            print("-" * 60)
    else:
        print("❌ No summaries found")

    conn.close()
    print(f"\n📊 Total entries displayed: {len(rows)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        print("🧹 Running cleanup mode...")
        clean_duplicates()
    else:
        print("🚀 Starting PDF analysis...")
        print("💡 Tip: Run with --clean flag to remove duplicates")
        main()
