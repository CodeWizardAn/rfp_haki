"""
RFP Analyzer
Processes scraped RFP PDFs through the extraction and analysis pipeline.
Uses the existing pdf_extraction and rfp_terms_matcher modules.
Generates per-RFP analysis reports.
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Import extraction modules
try:
    from pdf_extraction.pdf_extraction_manager import PDFExtractionManager
    PDF_MANAGER_AVAILABLE = True
except ImportError as e:
    PDF_MANAGER_AVAILABLE = False
    logger.warning(f"PDFExtractionManager not available: {e}")

try:
    from pdf_extraction.rfp_terms_matcher import RFPTermsMatcher
    TERMS_MATCHER_AVAILABLE = True
except ImportError as e:
    TERMS_MATCHER_AVAILABLE = False
    logger.warning(f"RFPTermsMatcher not available: {e}")

try:
    from pdf_extraction.pdf_text_extractor import PDFTextExtractor
    TEXT_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    TEXT_EXTRACTOR_AVAILABLE = False
    logger.warning(f"PDFTextExtractor not available: {e}")


class RFPAnalyzer:
    """
    Analyzes RFP PDFs using the existing extraction pipeline.
    Produces structured analysis output per RFP.
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or os.path.join(os.path.dirname(__file__), "analysis_output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extractors
        self.pdf_manager = None
        self.terms_matcher = None
        self.text_extractor = None
        
        if PDF_MANAGER_AVAILABLE:
            self.pdf_manager = PDFExtractionManager(str(self.output_dir / "uploads"))
            logger.info("✅ PDFExtractionManager loaded")
        
        if TERMS_MATCHER_AVAILABLE:
            try:
                self.terms_matcher = RFPTermsMatcher()
                logger.info("✅ RFPTermsMatcher loaded")
            except Exception as e:
                logger.warning(f"⚠️  RFPTermsMatcher init issue: {e}")
                self.terms_matcher = None
        
        if TEXT_EXTRACTOR_AVAILABLE:
            # PDFTextExtractor requires a pdf_path at init; we'll init per-file
            logger.info("✅ PDFTextExtractor available (initialized per-file)")
        
        self.analysis_results = {}
    
    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF using available extractors."""
        result = {
            "full_text": "",
            "page_info": {},
            "total_pages": 0,
            "total_chars": 0,
            "total_words": 0,
            "extraction_method": None,
        }
        
        # Method 1: PDFExtractionManager (PyPDF2-based)
        if self.pdf_manager:
            try:
                full_text, page_info = self.pdf_manager.extract_text_from_pdf(pdf_path)
                result["full_text"] = full_text
                result["page_info"] = page_info
                result["total_pages"] = len(page_info)
                result["total_chars"] = len(full_text)
                result["total_words"] = len(full_text.split())
                result["extraction_method"] = "PDFExtractionManager"
                return result
            except Exception as e:
                logger.warning(f"  PDFExtractionManager failed: {e}")
        
        # Method 2: pdfplumber-based extractor
        if TEXT_EXTRACTOR_AVAILABLE:
            try:
                extractor = PDFTextExtractor(pdf_path)
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    pages_text = []
                    page_info = {}
                    for i, page in enumerate(pdf.pages):
                        text = extractor.extract_text_from_page(page)
                        pages_text.append(text)
                        page_info[str(i+1)] = {
                            "char_count": len(text),
                            "word_count": len(text.split()),
                        }
                    full_text = "\n\n".join(pages_text)
                    result["full_text"] = full_text
                    result["page_info"] = page_info
                    result["total_pages"] = len(pdf.pages)
                    result["total_chars"] = len(full_text)
                    result["total_words"] = len(full_text.split())
                    result["extraction_method"] = "PDFTextExtractor (pdfplumber)"
                return result
            except Exception as e:
                logger.warning(f"  PDFTextExtractor failed: {e}")
        
        # Method 3: Fallback basic PyPDF2
        try:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    pages_text.append(text)
                full_text = "\n\n".join(pages_text)
                result["full_text"] = full_text
                result["total_pages"] = len(reader.pages)
                result["total_chars"] = len(full_text)
                result["total_words"] = len(full_text.split())
                result["extraction_method"] = "PyPDF2 (fallback)"
            return result
        except Exception as e:
            logger.error(f"  All extraction methods failed: {e}")
            return result
    
    def analyze_terms(self, text: str) -> Dict[str, Any]:
        """Analyze RFP text using RFPTermsMatcher with custom parsing to handle known bugs."""
        if not self.terms_matcher or not text.strip():
            return {"available": False, "reason": "Terms matcher not loaded or empty text"}
        
        try:
            import re
            
            # Direct field extraction since parse_rfp_text has a serialization bug
            # (find_term returns JSON string but parse_rfp_text treats it as dict)
            extracted_fields = {}
            unrecognized_fields = []
            matched_lines = 0
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                section = self.terms_matcher._detect_section(line)
                if section:
                    current_section = section
                    continue
                
                # Try field:value extraction
                if ':' in line or '/' in line:
                    parts = re.split(r'[:/]', line, 1)
                    if len(parts) == 2:
                        field_name = parts[0].strip()
                        field_value = parts[1].strip()
                        
                        term_result = self.terms_matcher.find_term(field_name)
                        if term_result:
                            matched_lines += 1
                            # find_term returns JSON string - parse it
                            if isinstance(term_result, str):
                                try:
                                    term_info = json.loads(term_result)
                                except (json.JSONDecodeError, TypeError):
                                    term_info = {"primary": field_name, "field_type": "text", "category": "general"}
                            else:
                                term_info = term_result
                            
                            primary_name = term_info.get('primary', field_name)
                            field_type = term_info.get('field_type', 'text')
                            category = term_info.get('category', 'general')
                            
                            extracted_value = self.terms_matcher.extract_field_value(field_value, field_type)
                            
                            extracted_fields[primary_name] = {
                                'value': extracted_value or field_value,
                                'original_text': line,
                                'field_type': field_type,
                                'category': category,
                                'section': current_section,
                            }
                        elif field_name and field_value:
                            unrecognized_fields.append({
                                'field': field_name, 
                                'value': field_value
                            })
            
            # Get database info
            try:
                db_info = self.terms_matcher.get_database_info()
            except Exception:
                db_info = {}
            
            return {
                "available": True,
                "parsed_data": {
                    "extracted_fields": extracted_fields,
                    "fields_count": len(extracted_fields),
                    "unrecognized_count": len(unrecognized_fields),
                    "total_lines": len(lines),
                    "matched_lines": matched_lines,
                    "fields_extracted": len(extracted_fields),
                },
                "validation": {},
                "database_info": {
                    "total_terms": db_info.get("total_terms", 0),
                    "categories": db_info.get("categories", []),
                },
            }
        except Exception as e:
            logger.error(f"  Terms analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {"available": False, "reason": str(e)}
    
    def generate_summary(self, rfp_id: str, extraction: Dict, terms_analysis: Dict, metadata: Dict) -> Dict:
        """Generate a comprehensive summary for one RFP."""
        summary = {
            "rfp_id": rfp_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "source": {
                "portal": metadata.get("source_portal", "Unknown"),
                "portal_id": metadata.get("source_portal_id", ""),
                "url": metadata.get("source_url", ""),
                "title": metadata.get("title", ""),
                "category": metadata.get("category", ""),
                "organization": metadata.get("organization", ""),
                "deadline": metadata.get("deadline", ""),
                "estimated_value": metadata.get("estimated_value", ""),
            },
            "extraction": {
                "method": extraction.get("extraction_method", "None"),
                "total_pages": extraction.get("total_pages", 0),
                "total_words": extraction.get("total_words", 0),
                "total_chars": extraction.get("total_chars", 0),
                "text_preview": extraction.get("full_text", "")[:500],
            },
            "terms_analysis": {},
            "key_requirements": [],
            "identified_sections": [],
        }
        
        if terms_analysis.get("available"):
            parsed = terms_analysis.get("parsed_data", {})
            extracted_fields = parsed.get("extracted_fields", {})
            
            summary["terms_analysis"] = {
                "terms_matched": parsed.get("fields_extracted", 0),
                "matched_lines": parsed.get("matched_lines", 0),
                "total_lines": parsed.get("total_lines", 0),
                "unrecognized_count": parsed.get("unrecognized_count", 0),
                "categories_found": list(set(
                    v.get("category", "") for v in extracted_fields.values()
                    if isinstance(v, dict)
                )),
            }
            
            # Extract key requirements from extracted fields
            for field_name, field_data in extracted_fields.items():
                if isinstance(field_data, dict):
                    summary["key_requirements"].append({
                        "field": field_name,
                        "value": field_data.get("value", ""),
                        "category": field_data.get("category", ""),
                        "section": field_data.get("section", ""),
                    })
                    section = field_data.get("section")
                    if section and section not in summary["identified_sections"]:
                        summary["identified_sections"].append(section)
            
            summary["validation"] = terms_analysis.get("validation", {})
        
        return summary
    
    def analyze_single_rfp(self, pdf_path: str, metadata: Dict = None) -> Dict:
        """
        Full analysis pipeline for a single RFP.
        
        Steps:
        1. Extract text from PDF
        2. Match RFP terms
        3. Generate structured summary
        4. Save per-RFP output
        """
        rfp_id = metadata.get("rfp_id", Path(pdf_path).stem) if metadata else Path(pdf_path).stem
        logger.info(f"\n{'─'*50}")
        logger.info(f"📄 Analyzing: {rfp_id} ({Path(pdf_path).name})")
        logger.info(f"{'─'*50}")
        
        if not os.path.exists(pdf_path):
            logger.error(f"  ❌ PDF not found: {pdf_path}")
            return {"rfp_id": rfp_id, "error": "PDF not found"}
        
        # Step 1: Extract text
        logger.info("  Step 1/3: Extracting text from PDF...")
        extraction = self.extract_text(pdf_path)
        logger.info(f"    → {extraction['total_pages']} pages, {extraction['total_words']} words")
        
        # Step 2: Analyze terms
        logger.info("  Step 2/3: Analyzing RFP terms & requirements...")
        terms_analysis = self.analyze_terms(extraction.get("full_text", ""))
        if terms_analysis.get("available"):
            parsed = terms_analysis.get("parsed_data", {})
            term_count = parsed.get("matched_terms_count", "N/A") if isinstance(parsed, dict) else "N/A"
            logger.info(f"    → Matched terms: {term_count}")
        else:
            logger.info(f"    → Terms analysis: {terms_analysis.get('reason', 'unavailable')}")
        
        # Step 3: Generate summary
        logger.info("  Step 3/3: Generating analysis report...")
        summary = self.generate_summary(rfp_id, extraction, terms_analysis, metadata or {})
        
        # Save individual report
        report_dir = self.output_dir / rfp_id
        report_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        report_path = report_dir / f"{rfp_id}_analysis.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        # Save extracted text
        text_path = report_dir / f"{rfp_id}_extracted_text.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(extraction.get("full_text", ""))
        
        # Save human-readable report
        readable_path = report_dir / f"{rfp_id}_report.txt"
        with open(readable_path, "w", encoding="utf-8") as f:
            f.write(self._format_readable_report(summary))
        
        logger.info(f"  ✅ Analysis saved to: {report_dir}")
        
        self.analysis_results[rfp_id] = summary
        return summary
    
    def analyze_all(self, scraped_rfps: List[Dict]) -> Dict[str, Any]:
        """
        Analyze all scraped RFPs. Returns consolidated results.
        """
        logger.info("=" * 60)
        logger.info("🔬 RFP Analyzer - Processing All Scraped RFPs")
        logger.info(f"   Total RFPs to analyze: {len(scraped_rfps)}")
        logger.info("=" * 60)
        
        results = {}
        success = 0
        failed = 0
        
        for rfp in scraped_rfps:
            pdf_path = rfp.get("local_pdf_path")
            if not pdf_path:
                logger.warning(f"  ⚠️  No local PDF for {rfp.get('rfp_id', '?')}, skipping")
                failed += 1
                continue
            
            try:
                result = self.analyze_single_rfp(pdf_path, metadata=rfp)
                results[rfp["rfp_id"]] = result
                if "error" not in result:
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"  ❌ Failed to analyze {rfp.get('rfp_id', '?')}: {e}")
                failed += 1
        
        # Save consolidated report
        consolidated = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_analyzed": len(results),
            "successful": success,
            "failed": failed,
            "per_portal_summary": self._per_portal_summary(scraped_rfps, results),
            "results": results,
        }
        
        consolidated_path = self.output_dir / "consolidated_analysis.json"
        with open(consolidated_path, "w", encoding="utf-8") as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False, default=str)
        
        # Save master readable report
        master_report_path = self.output_dir / "master_report.txt"
        with open(master_report_path, "w", encoding="utf-8") as f:
            f.write(self._format_master_report(consolidated))
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Analysis Complete: {success} succeeded, {failed} failed")
        logger.info(f"📁 Output: {self.output_dir}")
        logger.info(f"📋 Consolidated: {consolidated_path}")
        logger.info(f"📄 Master Report: {master_report_path}")
        logger.info(f"{'='*60}\n")
        
        return consolidated
    
    def _per_portal_summary(self, scraped_rfps: List[Dict], results: Dict) -> Dict:
        """Generate per-portal summary stats."""
        portals = {}
        for rfp in scraped_rfps:
            pid = rfp.get("source_portal_id", "unknown")
            pname = rfp.get("source_portal", "Unknown")
            if pid not in portals:
                portals[pid] = {"name": pname, "total": 0, "analyzed": 0, "rfps": []}
            portals[pid]["total"] += 1
            rid = rfp.get("rfp_id")
            if rid in results and "error" not in results[rid]:
                portals[pid]["analyzed"] += 1
            portals[pid]["rfps"].append(rid)
        return portals
    
    def _format_readable_report(self, summary: Dict) -> str:
        """Format a single RFP analysis as a readable text report."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"  RFP ANALYSIS REPORT: {summary.get('rfp_id', 'Unknown')}")
        lines.append("=" * 70)
        lines.append(f"  Generated: {summary.get('analysis_timestamp', '')}")
        lines.append("")
        
        src = summary.get("source", {})
        lines.append("  SOURCE INFORMATION")
        lines.append("  " + "-" * 40)
        lines.append(f"  Portal:       {src.get('portal', 'N/A')}")
        lines.append(f"  Title:        {src.get('title', 'N/A')}")
        lines.append(f"  Category:     {src.get('category', 'N/A')}")
        lines.append(f"  Organization: {src.get('organization', 'N/A')}")
        lines.append(f"  Deadline:     {src.get('deadline', 'N/A')}")
        lines.append(f"  Est. Value:   {src.get('estimated_value', 'N/A')}")
        lines.append("")
        
        ext = summary.get("extraction", {})
        lines.append("  DOCUMENT EXTRACTION")
        lines.append("  " + "-" * 40)
        lines.append(f"  Method:  {ext.get('method', 'N/A')}")
        lines.append(f"  Pages:   {ext.get('total_pages', 0)}")
        lines.append(f"  Words:   {ext.get('total_words', 0)}")
        lines.append(f"  Chars:   {ext.get('total_chars', 0)}")
        lines.append("")
        
        ta = summary.get("terms_analysis", {})
        lines.append("  TERMS ANALYSIS")
        lines.append("  " + "-" * 40)
        lines.append(f"  Terms Matched:    {ta.get('terms_matched', 'N/A')}")
        lines.append(f"  Categories Found: {', '.join(ta.get('categories_found', [])) or 'N/A'}")
        lines.append("")
        
        kf = ta.get("key_fields", {})
        if kf:
            lines.append("  KEY EXTRACTED FIELDS")
            lines.append("  " + "-" * 40)
            for k, v in kf.items():
                if v and str(v).strip():
                    lines.append(f"  {k}: {v}")
            lines.append("")
        
        sections = summary.get("identified_sections", [])
        if sections:
            lines.append("  IDENTIFIED SECTIONS")
            lines.append("  " + "-" * 40)
            for s in sections:
                lines.append(f"    • {s}")
            lines.append("")
        
        reqs = summary.get("key_requirements", [])
        if reqs:
            lines.append("  KEY REQUIREMENTS / MATCHED TERMS")
            lines.append("  " + "-" * 40)
            for r in reqs[:15]:
                if isinstance(r, dict):
                    lines.append(f"    • {r.get('term', r.get('name', str(r)))}")
                else:
                    lines.append(f"    • {r}")
            lines.append("")
        
        preview = ext.get("text_preview", "")
        if preview:
            lines.append("  TEXT PREVIEW (first 500 chars)")
            lines.append("  " + "-" * 40)
            for pline in preview.split("\n")[:15]:
                lines.append(f"  {pline}")
            lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def _format_master_report(self, consolidated: Dict) -> str:
        """Format the master consolidated report."""
        lines = []
        lines.append("=" * 70)
        lines.append("  MASTER RFP ANALYSIS REPORT")
        lines.append("  E-Procurement Portal Scraper & Analyzer")
        lines.append("=" * 70)
        lines.append(f"  Generated: {consolidated.get('analysis_timestamp', '')}")
        lines.append(f"  Total RFPs Analyzed: {consolidated.get('total_analyzed', 0)}")
        lines.append(f"  Successful: {consolidated.get('successful', 0)}")
        lines.append(f"  Failed: {consolidated.get('failed', 0)}")
        lines.append("")
        
        # Per-portal summary
        lines.append("  PER-PORTAL BREAKDOWN")
        lines.append("  " + "-" * 50)
        portal_summary = consolidated.get("per_portal_summary", {})
        for pid, info in portal_summary.items():
            lines.append(f"  {info['name']}:")
            lines.append(f"    Total: {info['total']} | Analyzed: {info['analyzed']}")
            lines.append(f"    RFPs: {', '.join(info.get('rfps', []))}")
            lines.append("")
        
        # Per-RFP summaries
        lines.append("  INDIVIDUAL RFP SUMMARIES")
        lines.append("  " + "=" * 50)
        results = consolidated.get("results", {})
        for rfp_id, result in results.items():
            src = result.get("source", {})
            ext = result.get("extraction", {})
            ta = result.get("terms_analysis", {})
            
            lines.append(f"\n  📄 {rfp_id}")
            lines.append(f"     Title:    {src.get('title', 'N/A')}")
            lines.append(f"     Portal:   {src.get('portal', 'N/A')}")
            lines.append(f"     Category: {src.get('category', 'N/A')}")
            lines.append(f"     Pages:    {ext.get('total_pages', 0)} | Words: {ext.get('total_words', 0)}")
            lines.append(f"     Terms:    {ta.get('terms_matched', 'N/A')} matched")
            lines.append(f"     Sections: {', '.join(result.get('identified_sections', [])) or 'None'}")
            lines.append("")
        
        lines.append("=" * 70)
        lines.append("  End of Report")
        lines.append("=" * 70)
        return "\n".join(lines)
