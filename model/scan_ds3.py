import fitz  # PyMuPDF

PDF_PATH = "DS3.pdf"

def scan_ds3_for_images():
    """Scan DS3.pdf to find pages with images"""
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    
    pages_with_images = []
    
    print(f"🔍 Scanning DS3.pdf - {total_pages} pages for images...")
    
    for page_num in range(1, total_pages + 1):
        page = doc[page_num - 1]
        image_list = page.get_images()
        
        if image_list:
            print(f"📸 Page {page_num}: Found {len(image_list)} image(s)")
            pages_with_images.append({
                'page': page_num,
                'image_count': len(image_list),
                'images': image_list
            })
            
            # Get basic info about each image
            for i, img in enumerate(image_list):
                print(f"   Image {i+1}: xref={img[0]}, width={img[2]}, height={img[3]}")
        else:
            print(f"📄 Page {page_num}: No images")
    
    doc.close()
    
    print(f"\n📊 Summary: Found images on {len(pages_with_images)} pages")
    return pages_with_images

if __name__ == "__main__":
    pages_with_images = scan_ds3_for_images()
    
    if pages_with_images:
        print("\n🎯 Pages with images in DS3.pdf:")
        for page_info in pages_with_images:
            print(f"  Page {page_info['page']}: {page_info['image_count']} images")
    else:
        print("❌ No images found in DS3.pdf")
