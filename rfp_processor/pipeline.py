"""
RFP Processor Pipeline
Main entry point - scrapes all portals, downloads PDFs, and runs analysis.
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import PortalScraper
from analyzer import RFPAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent


def run_pipeline(skip_scrape: bool = False, skip_download: bool = False, 
                 portal_filter: str = None, rfp_filter: str = None):
    """
    Execute the full RFP processing pipeline.
    
    Steps:
    1. Scrape all 5 e-procurement portals for RFP listings
    2. Download all RFP PDFs
    3. Extract text from each PDF
    4. Analyze RFP terms, requirements, and structure
    5. Generate per-RFP and consolidated reports
    """
    print("\n" + "=" * 70)
    print("  🔄 RFP PROCESSOR PIPELINE")
    print("  Scrape → Download → Extract → Analyze → Report")
    print("=" * 70 + "\n")
    
    scraper = PortalScraper(output_dir=str(BASE_DIR / "scraped_rfps"))
    analyzer = RFPAnalyzer(output_dir=str(BASE_DIR / "analysis_output"))
    
    # ── Phase 1: Scrape ──────────────────────────────────────────────────
    if skip_scrape:
        logger.info("⏭️  Skipping scrape, loading from manifest...")
        rfps = scraper.get_scraped_rfps()
        if not rfps:
            logger.error("❌ No scraped data found. Run without --skip-scrape first.")
            return
    else:
        logger.info("🕷️  Phase 1: Scraping all portals...")
        rfps = scraper.scrape_all_portals(download_pdfs=not skip_download)
    
    if not rfps:
        logger.error("❌ No RFPs found. Are the portals running?")
        print("\n💡 Start portals first:")
        print("   python e_procure_portals/launch_all_portals.py")
        return
    
    # Apply filters
    if portal_filter:
        rfps = [r for r in rfps if r.get("source_portal_id") == portal_filter]
        logger.info(f"🔍 Filtered to portal: {portal_filter} ({len(rfps)} RFPs)")
    
    if rfp_filter:
        rfps = [r for r in rfps if r.get("rfp_id") == rfp_filter]
        logger.info(f"🔍 Filtered to RFP: {rfp_filter}")
    
    # ── Phase 2: Analyze ─────────────────────────────────────────────────
    logger.info(f"\n🔬 Phase 2: Analyzing {len(rfps)} RFPs...")
    results = analyzer.analyze_all(rfps)
    
    # ── Phase 3: Summary ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  📊 PIPELINE COMPLETE - SUMMARY")
    print("=" * 70)
    print(f"  Total RFPs Scraped:   {len(rfps)}")
    print(f"  Successfully Analyzed: {results.get('successful', 0)}")
    print(f"  Failed:               {results.get('failed', 0)}")
    print()
    
    portal_summary = results.get("per_portal_summary", {})
    for pid, info in portal_summary.items():
        print(f"  {info['name']}: {info['analyzed']}/{info['total']} analyzed")
    
    print(f"\n  📁 Scraped PDFs:     {BASE_DIR / 'scraped_rfps'}")
    print(f"  📁 Analysis Output:  {BASE_DIR / 'analysis_output'}")
    print(f"  📋 Master Report:    {BASE_DIR / 'analysis_output' / 'master_report.txt'}")
    print(f"  📋 Consolidated JSON: {BASE_DIR / 'analysis_output' / 'consolidated_analysis.json'}")
    print("=" * 70 + "\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="RFP Processor Pipeline")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="Skip scraping, use previously scraped data")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip PDF downloads (if already downloaded)")
    parser.add_argument("--portal", type=str, default=None,
                        help="Only process RFPs from specific portal (e.g. portal_1)")
    parser.add_argument("--rfp", type=str, default=None,
                        help="Only process specific RFP (e.g. RFP17)")
    
    args = parser.parse_args()
    run_pipeline(
        skip_scrape=args.skip_scrape,
        skip_download=args.skip_download,
        portal_filter=args.portal,
        rfp_filter=args.rfp
    )


if __name__ == "__main__":
    main()
