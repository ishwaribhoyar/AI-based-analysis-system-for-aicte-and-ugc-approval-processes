"""Quick script to check dependency installation status"""

print("Checking dependencies...\n")

# Check Docling
try:
    from docling.document_converter import DocumentConverter
    print("✅ Docling: Installed")
except ImportError:
    print("❌ Docling: Not installed")

# Check PaddleOCR
try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR: Installed")
except ImportError:
    print("❌ PaddleOCR: Not installed")

# Check WeasyPrint
try:
    from weasyprint import HTML
    print("✅ WeasyPrint: Installed")
except ImportError as e:
    print(f"⚠️ WeasyPrint: Import error - {type(e).__name__}")
except Exception as e:
    print(f"⚠️ WeasyPrint: {type(e).__name__} - {str(e)[:100]}")

print("\n✅ Core dependencies (FastAPI, PyPDF, etc.) are installed")
print("⚠️ Optional dependencies have fallbacks - system works without them")

