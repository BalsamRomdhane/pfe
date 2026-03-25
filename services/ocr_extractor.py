from pdf2image import convert_from_path
import pytesseract

def extract_text_ocr(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for i, image in enumerate(images):
        page_text = pytesseract.image_to_string(image)
        print(f"===== OCR PAGE {i} =====")
        print(page_text[:500])
        text += page_text + "\n"
    print("===== RAW OCR TEXT =====")
    print("TEXT LENGTH:", len(text))
    print("TEXT PREVIEW:", text[:1000])
    print("LINES:", text.split("\n")[:20])
    if not text or len(text.strip()) < 50:
        print("ERROR: OCR extraction failed or text too short")
    return text
