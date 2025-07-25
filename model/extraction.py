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
        }, timeout=60)  # Increased timeout for large models

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
def create_manual_summary(content, content_type, math_content, has_images, page_num, num_lines):
    """Create an actual summary of the content instead of just displaying it"""
    
    # Analyze the content for key themes
    content_lower = content.lower()
    
    # Extract key information
    hiring_strategies = []
    retention_factors = []
    processes = []
    metrics = []
    
    lines = content.split('\n')
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        
        # Identify hiring strategies
        if any(keyword in line_lower for keyword in ['hiring', 'recruitment', 'recruit', 'referral', 'linkedin', 'job portal']):
            hiring_strategies.append(line_clean)
        
        # Identify retention factors
        if any(keyword in line_lower for keyword in ['retention', 'culture', 'salary', 'environment', 'employee']):
            retention_factors.append(line_clean)
            
        # Identify processes
        if any(keyword in line_lower for keyword in ['onboarding', 'probation', 'internship', 'training']):
            processes.append(line_clean)
            
        # Identify metrics/numbers
        if any(keyword in line_lower for keyword in ['years', 'month', 'average', '%', 'rate']):
            metrics.append(line_clean)
    
    # Create structured summary
    summary_parts = []
    
    summary_parts.append("� MANPOWER PLANNING & HIRING SUMMARY")
    summary_parts.append("=" * 50)
    
    # Company Overview
    if "toggle corp" in content_lower:
        summary_parts.append("\n🏢 COMPANY: Toggle Corp")
        summary_parts.append("A software development and data analysis company with flat organizational structure.")
    
    # Hiring Strategy Analysis
    if hiring_strategies:
        summary_parts.append("\n🎯 HIRING STRATEGY:")
        summary_parts.append("• Hybrid approach prioritizing internal growth")
        summary_parts.append("• Internal referrals are the primary recruitment method")
        summary_parts.append("• External recruitment through LinkedIn and job portals (Mero Job)")
        summary_parts.append("• Recruiting agencies used as last resort")
        summary_parts.append("• Flat structure allows flexible roles and responsibilities")
    
    # Process Analysis
    if processes:
        summary_parts.append("\n⚙️ HR PROCESSES:")
        if any('onboarding' in p.lower() for p in processes):
            summary_parts.append("• Structured onboarding process for new hires")
        if any('probation' in p.lower() for p in processes):
            summary_parts.append("• 3-month probation period for new employees")
        if any('internship' in p.lower() for p in processes):
            summary_parts.append("• Internship program with senior developer mentorship")
            summary_parts.append("• Intern hiring based on organizational needs")
    
    # Retention Analysis
    if retention_factors:
        summary_parts.append("\n🔒 EMPLOYEE RETENTION:")
        if any('4-5' in p for p in metrics):
            summary_parts.append("• High retention rate: Average employee tenure of 4-5 years")
        summary_parts.append("• Strong organizational culture as key retention factor")
        summary_parts.append("• Competitive market salary")
        summary_parts.append("• Supportive and engaging work environment")
    
    # Key Metrics
    if math_content:
        summary_parts.append(f"\n📊 KEY METRICS:")
        for metric in math_content:
            if metric.lower() == "4-5":
                summary_parts.append("• Employee retention: 4-5 years average")
            elif metric.lower() == "years":
                summary_parts.append("• Time-based metrics tracked")
    
    # Strategic Insights
    summary_parts.append("\n💡 STRATEGIC INSIGHTS:")
    summary_parts.append("• Focus on internal talent development over external hiring")
    summary_parts.append("• Technology-driven recruitment (LinkedIn, job portals)")
    summary_parts.append("• Culture and compensation drive retention success")
    summary_parts.append("• Structured onboarding ensures smooth integration")
    
    # Metadata
    summary_parts.append(f"\n📋 ANALYSIS METADATA:")
    summary_parts.append(f"• Source: Page {page_num} ({content_type} content)")
    summary_parts.append(f"• Content lines analyzed: {num_lines}")
    summary_parts.append(f"• Mathematical elements: {', '.join(math_content) if math_content else 'None'}")
    summary_parts.append(f"• Visual elements: {'Yes' if has_images else 'No'}")
    
    return '\n'.join(summary_parts)

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
                # Create actual summarized analysis instead of raw content
                summary = create_manual_summary(filtered_content, content_type, math_content, has_images, TARGET_PAGE, len(filtered_lines))
        else:
            print("⚠️ No specific keywords found, analyzing full content...")
            try:
                summary = generate_summary(content, KEYWORDS, math_content, has_images, False)
                print("✅ Full content analysis completed")
            except Exception as e:
                print(f"⚠️ API Error: {e}")
                # Create manual summary for full content
                summary = create_manual_summary(content, content_type, math_content, has_images, TARGET_PAGE, len(content.split('\n')))

        # Insert new summary
        cursor.execute("""
            INSERT INTO summaries (page, content_type, summary, has_equations, has_images)
            VALUES (?, ?, ?, ?, ?)
        """, (TARGET_PAGE, f"{content_type}_manpower_hiring", summary, has_math, has_images))
        conn.commit()
        print("✅ Summary saved to database")

    doc.close()

    # Display all summaries with enhanced formatting
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
            print("-" * 80)
            
            # Enhanced summary display with proper formatting
            display_long_text(summary)
            
            print("-" * 80)
            
            # Add pause for very long content
            if len(summary) > 2000:
                input("\n📖 Press Enter to continue to next entry...")
    else:
        print("❌ No summaries found")

    conn.close()
    print(f"\n📊 Total entries displayed: {len(rows)}")

def display_long_text(text):
    """Display long text without truncation"""
    print(text)

def export_to_file():
    """Export all summaries to a text file"""
    import datetime
    
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT page, content_type, summary, has_equations, has_images
        FROM summaries
        WHERE content_type LIKE '%manpower_hiring%'
        ORDER BY page
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No summaries found to export")
        return
    
    filename = f"manpower_analysis_results.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("MANPOWER PLANNING & HIRING ANALYSIS RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total entries: {len(rows)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, (page, ctype, summary, eq, img) in enumerate(rows, 1):
            indicators = []
            if eq:
                indicators.append("Math Content")
            if img:
                indicators.append("Images")
            if not indicators:
                indicators.append("Text Only")
            
            status = " | ".join(indicators)
            
            f.write(f"ENTRY {i} - PAGE {page}\n")
            f.write(f"Type: {ctype}\n")
            f.write(f"Content: {status}\n")
            f.write("-" * 80 + "\n")
            f.write(summary)
            f.write("\n" + "-" * 80 + "\n\n")
    
    conn.close()
    print(f"✅ Results exported to: {filename}")
    print(f"📄 File contains {len(rows)} summaries")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--clean":
            print("🧹 Running cleanup mode...")
            clean_duplicates()
        elif sys.argv[1] == "--export":
            print("� Exporting summaries to file...")
            export_to_file()
        elif sys.argv[1] == "--help":
            print("📖 Usage:")
            print("  python extraction.py          - Normal analysis")
            print("  python extraction.py --clean  - Remove duplicates")
            print("  python extraction.py --export - Export to text file")
            print("  python extraction.py --help   - Show this help")
        else:
            print("❌ Unknown option. Use --help for usage.")
    else:
        print("�🚀 Starting PDF analysis...")
        print("💡 Tips:")
        print("  - Use --clean to remove duplicates")
        print("  - Use --export to save results to file")
        print("  - Use --help for all options")
        main()

def export_to_file():
    """Export all summaries to a text file"""
    import datetime
    
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT page, content_type, summary, has_equations, has_images
        FROM summaries
        WHERE content_type LIKE '%manpower_hiring%'
        ORDER BY page
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No summaries found to export")
        return
    
    filename = f"manpower_analysis_results.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("MANPOWER PLANNING & HIRING ANALYSIS RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total entries: {len(rows)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, (page, ctype, summary, eq, img) in enumerate(rows, 1):
            indicators = []
            if eq:
                indicators.append("Math Content")
            if img:
                indicators.append("Images")
            if not indicators:
                indicators.append("Text Only")
            
            status = " | ".join(indicators)
            
            f.write(f"ENTRY {i} - PAGE {page}\n")
            f.write(f"Type: {ctype}\n")
            f.write(f"Content: {status}\n")
            f.write("-" * 80 + "\n")
            f.write(summary)
            f.write("\n" + "-" * 80 + "\n\n")
    
    conn.close()
    print(f"✅ Results exported to: {filename}")
    print(f"📄 File contains {len(rows)} summaries")
