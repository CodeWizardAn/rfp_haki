"""
RFP Processor Dashboard
Flask app to view scraping and analysis results.
"""
import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify, send_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
BASE_DIR = Path(__file__).parent
ANALYSIS_DIR = BASE_DIR / "analysis_output"
SCRAPED_DIR = BASE_DIR / "scraped_rfps"


def load_consolidated():
    path = ANALYSIS_DIR / "consolidated_analysis.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_manifest():
    path = SCRAPED_DIR / "scrape_manifest.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RFP Processor Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f1923; color: #e0e0e0; }
        
        .header {
            background: linear-gradient(135deg, #1a237e, #0d47a1);
            padding: 25px 40px;
            display: flex; align-items: center; justify-content: space-between;
        }
        .header h1 { font-size: 24px; color: white; }
        .header .subtitle { font-size: 13px; color: #90caf9; }
        .header .stats { display: flex; gap: 30px; }
        .header .stat-box { text-align: center; }
        .header .stat-num { font-size: 28px; font-weight: 700; color: #64ffda; }
        .header .stat-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #90caf9; }
        
        .content { max-width: 1300px; margin: 25px auto; padding: 0 20px; }
        
        .section { margin-bottom: 30px; }
        .section h2 { font-size: 18px; color: #64ffda; margin-bottom: 15px; border-bottom: 1px solid #1e3a5f; padding-bottom: 8px; }
        
        .portal-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 15px; }
        .portal-card {
            background: #162433;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #1e3a5f;
        }
        .portal-card h3 { font-size: 15px; color: #4fc3f7; margin-bottom: 8px; }
        .portal-card .count { font-size: 32px; font-weight: 700; color: #64ffda; }
        .portal-card .label { font-size: 11px; color: #78909c; }
        
        .rfp-table { width: 100%; border-collapse: collapse; }
        .rfp-table th { text-align: left; padding: 12px 15px; background: #1a2d3d; color: #4fc3f7; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .rfp-table td { padding: 12px 15px; border-bottom: 1px solid #1e3a5f; font-size: 13px; }
        .rfp-table tr:hover { background: #1a2d3d; }
        
        .badge { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; }
        .badge-success { background: #1b5e20; color: #a5d6a7; }
        .badge-warn { background: #e65100; color: #ffcc80; }
        .badge-info { background: #0d47a1; color: #90caf9; }
        
        .btn { display: inline-block; padding: 6px 14px; border-radius: 4px; text-decoration: none; font-size: 12px; }
        .btn-primary { background: #1565c0; color: white; }
        .btn-primary:hover { background: #1976d2; }
        
        .footer { text-align: center; padding: 20px; color: #546e7a; font-size: 11px; margin-top: 40px; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🔬 RFP Processor Dashboard</h1>
            <div class="subtitle">E-Procurement Portal Scraper & Analyzer</div>
        </div>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-num">{{ total_rfps }}</div>
                <div class="stat-label">Total RFPs</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{{ analyzed }}</div>
                <div class="stat-label">Analyzed</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">5</div>
                <div class="stat-label">Portals</div>
            </div>
        </div>
    </div>
    
    <div class="content">
        <div class="section">
            <h2>Portal Sources</h2>
            <div class="portal-grid">
                {% for pid, info in portal_summary.items() %}
                <div class="portal-card">
                    <h3>{{ info.name }}</h3>
                    <div class="count">{{ info.analyzed }}/{{ info.total }}</div>
                    <div class="label">RFPs Analyzed</div>
                    <div style="margin-top: 8px; font-size: 12px; color: #78909c;">
                        {{ ', '.join(info.rfps) }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="section">
            <h2>RFP Analysis Results</h2>
            <table class="rfp-table">
                <thead>
                    <tr>
                        <th>RFP ID</th>
                        <th>Title</th>
                        <th>Portal</th>
                        <th>Pages</th>
                        <th>Words</th>
                        <th>Terms</th>
                        <th>Sections</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for rfp_id, result in results.items() %}
                    <tr>
                        <td><strong>{{ rfp_id }}</strong></td>
                        <td>{{ result.source.title[:50] if result.source else 'N/A' }}...</td>
                        <td><span class="badge badge-info">{{ result.source.portal if result.source else 'N/A' }}</span></td>
                        <td>{{ result.extraction.total_pages if result.extraction else 0 }}</td>
                        <td>{{ result.extraction.total_words if result.extraction else 0 }}</td>
                        <td>
                            {% if result.terms_analysis and result.terms_analysis.terms_matched %}
                            <span class="badge badge-success">{{ result.terms_analysis.terms_matched }}</span>
                            {% else %}
                            <span class="badge badge-warn">N/A</span>
                            {% endif %}
                        </td>
                        <td>{{ (result.identified_sections|length) if result.identified_sections else 0 }}</td>
                        <td>
                            <a href="/api/rfp/{{ rfp_id }}" class="btn btn-primary">View JSON</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="footer">
        RFP Processor Dashboard | Generated {{ timestamp }} | Powered by Haki FMCG
    </div>
</body>
</html>
"""


@app.route("/")
def dashboard():
    data = load_consolidated()
    if not data:
        return "<h1>No analysis data yet. Run the pipeline first.</h1><p><code>python rfp_processor/pipeline.py</code></p>"
    
    return render_template_string(
        DASHBOARD_HTML,
        total_rfps=data.get("total_analyzed", 0),
        analyzed=data.get("successful", 0),
        portal_summary=data.get("per_portal_summary", {}),
        results=data.get("results", {}),
        timestamp=data.get("analysis_timestamp", ""),
    )


@app.route("/api/results")
def api_results():
    data = load_consolidated()
    if not data:
        return jsonify({"error": "No analysis data"}), 404
    return jsonify(data)


@app.route("/api/rfp/<rfp_id>")
def api_rfp_detail(rfp_id):
    data = load_consolidated()
    if not data:
        return jsonify({"error": "No analysis data"}), 404
    result = data.get("results", {}).get(rfp_id)
    if not result:
        return jsonify({"error": "RFP not found"}), 404
    return jsonify(result)


@app.route("/api/manifest")
def api_manifest():
    data = load_manifest()
    if not data:
        return jsonify({"error": "No scrape manifest"}), 404
    return jsonify(data)


@app.route("/report/<rfp_id>")
def rfp_report(rfp_id):
    report_path = ANALYSIS_DIR / rfp_id / f"{rfp_id}_report.txt"
    if report_path.exists():
        return send_file(str(report_path), mimetype="text/plain")
    return "Report not found", 404


if __name__ == "__main__":
    print("\n🔬 RFP Processor Dashboard")
    print("   http://localhost:5010\n")
    app.run(host="0.0.0.0", port=5010, debug=True)
