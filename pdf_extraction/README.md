# PDF Text Extraction Tool for RFP Documents

Comprehensive Python solution for extracting all text, tables, and structured data from PDF files, with special focus on RFP (Request for Proposal) documents.

## ✨ New Feature: Multilingual Support! 🌐

Now extract and analyze RFP terms in **3 languages**:
- 🇬🇧 **English** (240+ terms)
- 🇮🇳 **Hindi** (200+ terms)
- 🇮🇳 **Marathi** (200+ terms)

[👉 Quick Start Guide](MULTILINGUAL_QUICKSTART.md) | [📚 Full Documentation](MULTILINGUAL_FEATURE.md)

## Features

✅ **Complete Text Extraction** - Extract all text from any PDF  
✅ **Table Extraction** - Automatically detect and extract tables  
✅ **Page Markers** - Clear page boundaries in extracted text  
✅ **RFP Section Detection** - Automatically identify common RFP sections  
✅ **Batch Processing** - Extract multiple PDFs at once  
✅ **JSON Export** - Structured data export with metadata  
✅ **Selective Extraction** - Extract specific pages only  
✅ **Metadata Extraction** - Get document metadata and properties  
✅ **Flexible Output** - Save as .txt, .json, or use programmatically  
✅ **🌐 Multilingual Analysis** - Extract RFP terms in English, Hindi, Marathi  
✅ **Web Interface** - Easy-to-use Flask web application  
✅ **REST API** - Full API for programmatic access  

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install pdfplumber directly:

```bash
pip install pdfplumber
```

### 2. Verify Installation

```python
import pdfplumber
print("pdfplumber installed successfully")
```

## Quick Start

### Web Application (Easiest)

```bash
# Start the web application
python app.py

# Or on Windows
python run.bat

# Open browser: http://localhost:5000
```

Then:
1. Upload a PDF
2. Choose extraction type:
   - Text Extraction
   - RFP Analysis (English)
   - Extract Sections
   - **🌐 Multilingual Analysis** (NEW!)
3. For multilingual: Select languages (English, Hindi, Marathi)
4. Click Extract
5. View results and download

### Method 1: Simple Text Extraction (Python)

```python
from rfp_extractor import extract_pdf_simple

# Extract text from PDF
text = extract_pdf_simple("my_document.pdf")

# Or save directly to file
text = extract_pdf_simple("my_document.pdf", output_path="output.txt")
```

### Method 2: Multilingual Analysis (NEW!)

```python
from multilingual_rfp_extractor import MultilingualRFPAnalyzer

# Create analyzer
analyzer = MultilingualRFPAnalyzer()

# Get all text from PDF
from rfp_extractor import RFPExtractor
extractor = RFPExtractor("document.pdf")
text = extractor.extract_all_text_and_tables()

# Analyze in all languages
results = analyzer.analyze_multilingual(text)

# Get results per language
english_results = results['english']
hindi_results = results['hindi']
marathi_results = results['marathi']

print(f"English terms found: {english_results['total_terms_found']}")
print(f"Hindi terms found: {hindi_results['total_terms_found']}")
print(f"Marathi terms found: {marathi_results['total_terms_found']}")
```

### Method 3: English RFP Analysis

```python
from rfp_extractor import extract_pdf_with_tables

# Extract all text and tables
text = extract_pdf_with_tables("my_document.pdf", output_path="output.txt")
```

### Method 4: RFP-Specific Extraction

```python
from rfp_extractor import RFPExtractor

# Initialize extractor
extractor = RFPExtractor("rfp_document.pdf")

# Extract and save
extractor.save_extracted_text(include_tables=True)

# Print summary
extractor.print_extraction_summary()
```

### Method 5: Advanced Features

```python
from pdf_text_extractor import PDFTextExtractor

# Initialize
extractor = PDFTextExtractor("document.pdf")

# Extract all text
all_text = extractor.extract_all_text(include_tables=True)

# Extract specific pages
text = extractor.extract_with_filter(page_numbers=[1, 2, 5])

# Get metadata
metadata = extractor.extract_metadata()

# Save as JSON
extractor.extract_json_to_file(include_tables=True)
```

## Detailed API Reference

### RFPExtractor Class

**Simple Extractions:**

```python
extractor = RFPExtractor("document.pdf")

# Extract all text without tables
text = extractor.extract_all_text_simple()

# Extract with page markers
text = extractor.extract_with_page_markers()

# Extract text and tables together
text = extractor.extract_all_text_and_tables()
```

**File Operations:**

```python
# Save text to file (returns file path)
output_file = extractor.save_extracted_text(
    output_path="output.txt",
    include_tables=True
)

# Save text by RFP sections
section_files = extractor.save_extracted_by_sections(
    output_dir="./sections",
    include_tables=True
)
# Returns: {'section_name': 'file_path', ...}
```

**Section Detection:**

```python
# Get full extracted text
text = extractor.extract_all_text_and_tables()

# Identify sections
sections = extractor.identify_sections(text)
# Returns: {'executive_summary': [line_nums], 'requirements': [line_nums], ...}

# Extract specific section
section_text = extractor.extract_section_text(text, 'requirements')
```

**Utilities:**

```python
# Print extraction summary
extractor.print_extraction_summary(include_tables=True)
```

### PDFTextExtractor Class

**Advanced Features:**

```python
extractor = PDFTextExtractor("document.pdf")

# Extract structured data as dictionary
data = extractor.extract_as_json(include_tables=True)

# Save as JSON file
json_file = extractor.extract_json_to_file()

# Extract specific pages
text = extractor.extract_with_filter(
    page_numbers=[1, 3, 5],
    include_tables=True
)

# Get metadata
metadata = extractor.extract_metadata()
print(metadata)
# Returns: {
#     'document_name': 'file.pdf',
#     'total_pages': 10,
#     'page_width': 612,
#     'page_height': 792,
#     'pdf_metadata': {...}
# }
```

### Batch Processing

**Extract all PDFs in a directory:**

```python
from rfp_extractor import batch_extract_all_pdfs

# Extract all PDFs in directory
output_files = batch_extract_all_pdfs(
    directory="./pdf_directory",
    include_tables=True
)

print(f"Processed {len(output_files)} files")
for file in output_files:
    print(f"  - {file}")
```

## Common RFP Sections Detected

The tool automatically recognizes these common RFP sections:

- **Executive Summary** - High-level overview
- **Background** - Company and client background
- **Requirements** - Functional and technical requirements
- **Scope** - Project scope and boundaries
- **Timeline** - Project schedule
- **Budget** - Pricing and financial terms
- **Evaluation** - Selection criteria
- **Terms** - Terms and conditions
- **Contact** - Contact information
- **Appendix** - Attachments and exhibits

## Usage Examples

### Example 1: Extract RFP and Save Everything

```python
from rfp_extractor import RFPExtractor

# Create extractor
extractor = RFPExtractor("rfp_2024.pdf")

# Extract and save everything
text = extractor.extract_all_text_and_tables()

# Save to file
extractor.save_extracted_text(output_path="rfp_2024_extracted.txt")

# Print summary
extractor.print_extraction_summary()
```

### Example 2: Extract Specific RFP Sections

```python
from rfp_extractor import RFPExtractor

extractor = RFPExtractor("rfp_2024.pdf")

# Get full text
text = extractor.extract_all_text_and_tables()

# Extract requirements section only
requirements = extractor.extract_section_text(text, 'requirements')

# Save to file
with open("requirements.txt", "w") as f:
    f.write(requirements)
```

### Example 3: Batch Extract Multiple RFPs

```python
from rfp_extractor import batch_extract_all_pdfs
import os

# Create output directory
os.makedirs("extracted_rfps", exist_ok=True)

# Extract all PDFs in directory
batch_extract_all_pdfs(directory="./rfp_documents", include_tables=True)

# All extracted files saved to current directory with _extracted_text.txt suffix
```

### Example 4: Extract and Analyze

```python
from pdf_text_extractor import PDFTextExtractor
import json

# Extract as JSON
extractor = PDFTextExtractor("document.pdf")
data = extractor.extract_as_json(include_tables=True)

# Access structured data
print(f"Total pages: {data['total_pages']}")

for page in data['pages'][:3]:  # First 3 pages
    print(f"Page {page['page_number']}: {page['text_count']} characters")

# Save for later processing
with open("extracted_data.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Example 5: Extract Specific Pages

```python
from pdf_text_extractor import PDFTextExtractor

extractor = PDFTextExtractor("document.pdf")

# Extract pages 1, 2, and 5
text = extractor.extract_with_filter(page_numbers=[1, 2, 5])

# Save to file
with open("selected_pages.txt", "w") as f:
    f.write(text)
```

## File Structure

```
pdf_extraction/
├── pdf_text_extractor.py    # Advanced extraction with structured data
├── rfp_extractor.py         # RFP-specific extraction and section detection
├── examples.py              # Usage examples and patterns
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Output Formats

### Text Format (.txt)

```
================================================================================
PAGE 1
================================================================================

[Full page text here]

---TABLES ON THIS PAGE---

TABLE 1:
Header1 | Header2 | Header3
Row1Col1 | Row1Col2 | Row1Col3
Row2Col1 | Row2Col2 | Row2Col3

================================================================================
PAGE 2
================================================================================
...
```

### JSON Format (.json)

```json
{
  "document_name": "example.pdf",
  "document_path": "/path/to/example.pdf",
  "total_pages": 5,
  "pages": [
    {
      "page_number": 1,
      "page_height": 792,
      "page_width": 612,
      "text": "Page content here...",
      "tables": [
        [
          ["Header1", "Header2"],
          ["Row1Col1", "Row1Col2"]
        ]
      ],
      "text_count": 1234
    }
  ]
}
```

## Logging

The tool includes comprehensive logging. To see detailed logs:

```python
import logging

# Set to DEBUG for more details
logging.basicConfig(level=logging.DEBUG)

# Now run extraction
from rfp_extractor import RFPExtractor
extractor = RFPExtractor("document.pdf")
text = extractor.extract_all_text_and_tables()
```

Log levels used:
- `INFO` - General operations (extraction started, files saved, etc.)
- `WARNING` - Non-critical issues (could not extract tables, section not found)
- `ERROR` - Critical issues (file not found, extraction failed)

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pdfplumber'"

**Solution:** Install pdfplumber
```bash
pip install pdfplumber
```

### Issue: No text extracted from PDF

**Possible Causes:**
- PDF is image-based (scanned document) - pdfplumber cannot extract text from images
- PDF has encoding issues
- PDF is password protected

**Solutions:**
- Use OCR tool (Tesseract, Pytesseract) for scanned PDFs
- Check if PDF is corrupted
- Remove password protection

### Issue: Tables not extracting correctly

**Possible Causes:**
- Tables have complex formatting
- Tables use non-standard structures

**Solutions:**
- Check raw page extraction: `page.extract_text()`
- Try `include_tables=False` and process manually
- Inspect page layout with: `page.extract_text(layout=True)`

### Issue: Section detection not working

**Solution:** Sections are detected using regex patterns. For non-standard RFPs:

```python
extractor = RFPExtractor("document.pdf")
text = extractor.extract_all_text_and_tables()

# Manually find sections
import re
matches = re.finditer(r'your_section_header', text, re.IGNORECASE)
for match in matches:
    print(f"Found at position: {match.start()}")
```

## Performance Tips

1. **Large PDFs:** Extract specific pages instead of all:
   ```python
   text = extractor.extract_with_filter(page_numbers=[1, 2, 3])
   ```

2. **Skip Tables:** If you don't need tables:
   ```python
   text = extractor.extract_all_text_simple()
   ```

3. **Batch Processing:** Extract multiple files efficiently:
   ```python
   from rfp_extractor import batch_extract_all_pdfs
   batch_extract_all_pdfs("./pdfs")
   ```

## Advanced Usage

### Custom Section Detection

```python
from rfp_extractor import RFPExtractor
import re

extractor = RFPExtractor("document.pdf")
text = extractor.extract_all_text_and_tables()

# Custom regex pattern
pattern = r'custom_section_header'
matches = list(re.finditer(pattern, text, re.IGNORECASE))

for match in matches:
    start = match.start()
    print(f"Found custom section at position {start}")
```

### Direct pdfplumber Usage

For even more control, use pdfplumber directly:

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        # Extract text
        text = page.extract_text()
        
        # Extract with layout
        text_layout = page.extract_text(layout=True)
        
        # Extract tables with options
        tables = page.extract_tables({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines"
        })
        
        # Extract text by position
        crops = page.crop((0, 0, 300, 300))
        text_cropped = crops.extract_text()
```

## Requirements

- Python 3.6+
- pdfplumber >= 0.9.0

## License

This tool is provided as-is for educational and commercial use.

## Support

For issues or questions:

1. Check the examples.py file for usage patterns
2. Review the docstrings in source files
3. Enable DEBUG logging for detailed information
4. Check pdfplumber documentation: https://github.com/jsvine/pdfplumber

## Version History

- **v1.0** (2024)
  - Initial release
  - Complete text extraction
  - Table extraction
  - RFP section detection
  - Batch processing
  - JSON export

---

**Happy extracting! 📄**
