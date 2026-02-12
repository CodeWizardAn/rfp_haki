"""
RFP Portal Scraper
Scrapes RFP documents from all 5 e-procurement portals,
downloads PDFs, and stores metadata for analysis.
"""
import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Portal endpoints
PORTAL_ENDPOINTS = [
    {"portal_id": "portal_1", "name": "GovProcure India",    "base_url": "http://localhost:5001"},
    {"portal_id": "portal_2", "name": "TenderBazaar",         "base_url": "http://localhost:5002"},
    {"portal_id": "portal_3", "name": "eProcure Central",     "base_url": "http://localhost:5003"},
    {"portal_id": "portal_4", "name": "BidConnect",           "base_url": "http://localhost:5004"},
    {"portal_id": "portal_5", "name": "SmartTender Hub",      "base_url": "http://localhost:5005"},
]


class PortalScraper:
    """
    Scrapes RFP listings and downloads PDFs from e-procurement portals.
    Supports both API-based and HTML scraping approaches.
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or os.path.join(os.path.dirname(__file__), "scraped_rfps"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HakiFMCG-RFPProcessor/1.0",
            "Accept": "application/json, text/html"
        })
        self.scraped_data = []  # All scraped RFP records
        
    def scrape_portal_api(self, portal: Dict) -> List[Dict]:
        """Scrape RFPs from a portal using its JSON API."""
        base_url = portal["base_url"]
        portal_name = portal["name"]
        
        logger.info(f"📡 Scraping {portal_name} ({base_url})...")
        
        try:
            # Fetch RFP listing
            resp = self.session.get(f"{base_url}/api/rfps", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            rfps = data.get("rfps", [])
            logger.info(f"   Found {len(rfps)} RFPs on {portal_name}")
            
            scraped = []
            for rfp in rfps:
                rfp_record = {
                    "rfp_id": rfp["rfp_id"],
                    "filename": rfp["filename"],
                    "title": rfp["title"],
                    "category": rfp["category"],
                    "organization": rfp["organization"],
                    "publish_date": rfp["publish_date"],
                    "deadline": rfp["deadline"],
                    "status": rfp["status"],
                    "estimated_value": rfp["estimated_value"],
                    "location": rfp["location"],
                    "source_portal": portal_name,
                    "source_portal_id": portal["portal_id"],
                    "source_url": f"{base_url}/rfp/{rfp['rfp_id']}",
                    "download_url": f"{base_url}/download/{rfp['rfp_id']}",
                    "scraped_at": datetime.now().isoformat(),
                }
                scraped.append(rfp_record)
            
            return scraped
            
        except requests.ConnectionError:
            logger.error(f"   ❌ Cannot connect to {portal_name} at {base_url}")
            return []
        except Exception as e:
            logger.error(f"   ❌ Error scraping {portal_name}: {e}")
            return []
    
    def scrape_portal_html(self, portal: Dict) -> List[Dict]:
        """
        Fallback HTML scraper - parses portal homepage for RFP links.
        Used when API is not available.
        """
        base_url = portal["base_url"]
        portal_name = portal["name"]
        
        logger.info(f"🔍 HTML-scraping {portal_name} ({base_url})...")
        
        try:
            resp = self.session.get(base_url, timeout=10)
            resp.raise_for_status()
            html = resp.text
            
            # Simple regex-based extraction of RFP links
            import re
            rfp_links = re.findall(r'href="/rfp/(RFP\d+)"', html)
            download_links = re.findall(r'href="/download/(RFP\d+)"', html)
            
            scraped = []
            for rfp_id in set(rfp_links):
                rfp_record = {
                    "rfp_id": rfp_id,
                    "filename": f"{rfp_id}.pdf",
                    "title": f"RFP Document - {rfp_id}",
                    "source_portal": portal_name,
                    "source_portal_id": portal["portal_id"],
                    "source_url": f"{base_url}/rfp/{rfp_id}",
                    "download_url": f"{base_url}/download/{rfp_id}",
                    "scraped_at": datetime.now().isoformat(),
                }
                scraped.append(rfp_record)
            
            logger.info(f"   Found {len(scraped)} RFPs via HTML parsing")
            return scraped
            
        except Exception as e:
            logger.error(f"   ❌ HTML scraping failed for {portal_name}: {e}")
            return []
    
    def download_rfp_pdf(self, rfp_record: Dict) -> Optional[str]:
        """Download RFP PDF from portal and save locally."""
        rfp_id = rfp_record["rfp_id"]
        portal_id = rfp_record["source_portal_id"]
        download_url = rfp_record["download_url"]
        
        # Create portal-specific subfolder
        portal_dir = self.output_dir / portal_id
        portal_dir.mkdir(exist_ok=True)
        
        pdf_path = portal_dir / f"{rfp_id}.pdf"
        
        if pdf_path.exists():
            logger.info(f"   📄 {rfp_id} already downloaded, skipping")
            rfp_record["local_pdf_path"] = str(pdf_path)
            return str(pdf_path)
        
        try:
            resp = self.session.get(download_url, timeout=30)
            resp.raise_for_status()
            
            with open(pdf_path, "wb") as f:
                f.write(resp.content)
            
            file_size = os.path.getsize(pdf_path)
            rfp_record["local_pdf_path"] = str(pdf_path)
            rfp_record["file_size_bytes"] = file_size
            logger.info(f"   ⬇️  Downloaded {rfp_id} ({file_size:,} bytes)")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"   ❌ Failed to download {rfp_id}: {e}")
            return None
    
    def scrape_all_portals(self, download_pdfs: bool = True) -> List[Dict]:
        """
        Scrape all 5 portals and optionally download PDFs.
        Returns list of all scraped RFP records.
        """
        logger.info("=" * 60)
        logger.info("🕷️  RFP Portal Scraper - Starting Full Scan")
        logger.info("=" * 60)
        
        all_rfps = []
        
        for portal in PORTAL_ENDPOINTS:
            # Try API first, fall back to HTML
            rfps = self.scrape_portal_api(portal)
            if not rfps:
                rfps = self.scrape_portal_html(portal)
            
            if download_pdfs and rfps:
                logger.info(f"   📥 Downloading PDFs from {portal['name']}...")
                for rfp in rfps:
                    self.download_rfp_pdf(rfp)
            
            all_rfps.extend(rfps)
        
        self.scraped_data = all_rfps
        
        # Save manifest
        manifest_path = self.output_dir / "scrape_manifest.json"
        manifest = {
            "scrape_timestamp": datetime.now().isoformat(),
            "total_rfps": len(all_rfps),
            "portals_scraped": len(PORTAL_ENDPOINTS),
            "rfps": all_rfps
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Scraping Complete: {len(all_rfps)} RFPs from {len(PORTAL_ENDPOINTS)} portals")
        logger.info(f"📁 Saved to: {self.output_dir}")
        logger.info(f"📋 Manifest: {manifest_path}")
        logger.info(f"{'='*60}\n")
        
        return all_rfps
    
    def get_scraped_rfps(self) -> List[Dict]:
        """Return all scraped RFP records."""
        # Try loading from manifest if empty
        if not self.scraped_data:
            manifest_path = self.output_dir / "scrape_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, "r") as f:
                    data = json.load(f)
                    self.scraped_data = data.get("rfps", [])
        return self.scraped_data


if __name__ == "__main__":
    scraper = PortalScraper()
    rfps = scraper.scrape_all_portals(download_pdfs=True)
    
    print(f"\n📊 Summary:")
    for portal in PORTAL_ENDPOINTS:
        portal_rfps = [r for r in rfps if r["source_portal_id"] == portal["portal_id"]]
        print(f"  {portal['name']}: {len(portal_rfps)} RFPs")
