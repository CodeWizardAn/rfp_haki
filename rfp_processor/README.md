# RFP Processor

## Overview
Web scraper and analysis pipeline that extracts RFPs from the 5 e-procurement portals and processes them through the existing RFP analysis modules.

## Architecture

```
rfp_processor/
├── scraper.py          # Web scraper for all 5 portals (API + HTML fallback)
├── analyzer.py         # RFP analysis using pdf_extraction modules
├── pipeline.py         # Main entry point - full scrape→analyze pipeline
├── dashboard.py        # Flask dashboard to view results (port 5010)
├── scraped_rfps/       # Downloaded PDFs organized by portal
│   ├── portal_1/
│   ├── portal_2/
│   ├── ...
│   └── scrape_manifest.json
└── analysis_output/    # Analysis results
    ├── RFP17/
    │   ├── RFP17_analysis.json
    │   ├── RFP17_extracted_text.txt
    │   └── RFP17_report.txt
    ├── ...
    ├── consolidated_analysis.json
    └── master_report.txt
```

## Usage

### Prerequisites
Make sure the 5 portals are running first:
```bash
python e_procure_portals/launch_all_portals.py
```

### Run Full Pipeline
```bash
python rfp_processor/pipeline.py
```

### Options
```bash
# Skip scraping (reuse previous scrape)
python rfp_processor/pipeline.py --skip-scrape

# Only process one portal
python rfp_processor/pipeline.py --portal portal_1

# Only process one RFP
python rfp_processor/pipeline.py --rfp RFP17
```

### View Results Dashboard
```bash
python rfp_processor/dashboard.py
# Open http://localhost:5010
```

## Pipeline Flow
```
Portal 1 (5001) ─┐
Portal 2 (5002) ─┤
Portal 3 (5003) ─┼─► Scraper ─► Download PDFs ─► Extract Text ─► Match Terms ─► Reports
Portal 4 (5004) ─┤                                                                   │
Portal 5 (5005) ─┘                                                                   ▼
                                                                          Per-RFP Analysis JSON
                                                                          Extracted Text Files
                                                                          Readable Reports
                                                                          Consolidated Report
                                                                          Dashboard (5010)
```

## Output Per RFP
Each RFP generates:
1. **JSON Analysis** - Structured data with extracted fields, matched terms, sections
2. **Extracted Text** - Full text extracted from PDF
3. **Readable Report** - Human-friendly text report with key findings

## API Endpoints (Dashboard)
- `GET /` - Dashboard UI
- `GET /api/results` - Full consolidated analysis JSON
- `GET /api/rfp/<rfp_id>` - Individual RFP analysis
- `GET /api/manifest` - Scrape manifest
- `GET /report/<rfp_id>` - Download text report
