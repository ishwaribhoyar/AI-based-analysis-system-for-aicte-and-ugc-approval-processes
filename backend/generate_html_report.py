"""
Generate a beautiful HTML report from test results.
"""

import json
from pathlib import Path
from datetime import datetime


def generate_html_report(data: dict, output_path: str = None) -> str:
    """Generate an HTML report from the test results data."""
    
    # Build blocks table rows
    blocks_html = ""
    for block in data.get("blocks", []):
        present_icon = "✅" if block["is_present"] else "❌"
        confidence = f"{block['confidence']:.1%}" if block['confidence'] else "N/A"
        status_badges = ""
        if block.get("is_outdated"):
            status_badges += '<span class="badge badge-warning">OUTDATED</span>'
        if block.get("is_invalid"):
            status_badges += '<span class="badge badge-danger">INVALID</span>'
        if not status_badges:
            status_badges = '<span class="badge badge-success">OK</span>'
        
        blocks_html += f"""
        <tr>
            <td class="block-name">{block['name']}</td>
            <td class="text-center">{present_icon}</td>
            <td class="text-center">{confidence}</td>
            <td class="text-center">{block['extracted_fields_count']}</td>
            <td class="text-center">{status_badges}</td>
        </tr>
        """
    
    # Build KPI cards
    kpis_html = ""
    for kpi in data.get("kpis", []):
        value = kpi["value"]
        if isinstance(value, (int, float)):
            value_str = f"{value:.2f}"
            if value >= 80:
                kpi_class = "kpi-excellent"
                icon = "🟢"
            elif value >= 50:
                kpi_class = "kpi-good"
                icon = "🟡"
            else:
                kpi_class = "kpi-poor"
                icon = "🔴"
        else:
            value_str = str(value)
            kpi_class = "kpi-neutral"
            icon = "⚪"
        
        kpis_html += f"""
        <div class="kpi-card {kpi_class}">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value_str}</div>
            <div class="kpi-name">{kpi['name']}</div>
        </div>
        """
    
    # Build sufficiency section
    suff = data.get("sufficiency", {})
    suff_pct = suff.get("percentage", 0)
    if suff_pct >= 80:
        suff_class = "progress-excellent"
    elif suff_pct >= 50:
        suff_class = "progress-good"
    else:
        suff_class = "progress-poor"
    
    missing_blocks = suff.get("missing_blocks", [])
    missing_html = ""
    if missing_blocks:
        missing_html = f"""
        <div class="missing-blocks">
            <strong>⚠️ Missing Blocks:</strong> {', '.join(missing_blocks)}
        </div>
        """
    
    penalties = suff.get("penalty_breakdown", {})
    penalty_html = ""
    if any(v > 0 for v in penalties.values()):
        penalty_html = f"""
        <div class="penalties">
            <strong>📉 Penalties:</strong>
            Outdated: {penalties.get('outdated', 0)} |
            Low Quality: {penalties.get('low_quality', 0)} |
            Invalid: {penalties.get('invalid', 0)}
        </div>
        """
    
    # Build compliance flags
    flags_html = ""
    for flag in data.get("compliance_flags", []):
        severity = flag["severity"].upper()
        if severity in ["HIGH", "CRITICAL"]:
            flag_class = "flag-critical"
            sev_icon = "🔴"
        elif severity == "MEDIUM":
            flag_class = "flag-warning"
            sev_icon = "🟡"
        else:
            flag_class = "flag-info"
            sev_icon = "🟢"
        
        flags_html += f"""
        <div class="compliance-flag {flag_class}">
            <div class="flag-header">
                <span class="flag-icon">{sev_icon}</span>
                <span class="flag-severity">[{severity}]</span>
                <span class="flag-title">{flag['title']}</span>
            </div>
            <div class="flag-body">
                <p><strong>Reason:</strong> {flag['reason']}</p>
                <p><strong>Recommendation:</strong> {flag['recommendation']}</p>
            </div>
        </div>
        """
    
    if not flags_html:
        flags_html = '<div class="no-flags">✅ No compliance issues detected!</div>'
    
    # Build errors section
    errors_html = ""
    if data.get("errors"):
        errors_list = "".join([f"<li>{e}</li>" for e in data["errors"]])
        errors_html = f"""
        <div class="errors-section">
            <h2>❌ Errors</h2>
            <ul>{errors_list}</ul>
        </div>
        """
    
    # Status
    status = data.get("status", "unknown").upper()
    status_class = "status-success" if status == "COMPLETED" else "status-error"
    status_icon = "✅" if status == "COMPLETED" else "❌"
    
    batch_id = data.get("batch_id", "N/A")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Analysis Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e8e8e8;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
            border-radius: 20px;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }}
        
        .header-meta {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
            color: #a0a0a0;
            font-size: 0.9rem;
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        
        .status-success {{
            background: linear-gradient(135deg, #00c853, #00e676);
            color: #1a1a2e;
        }}
        
        .status-error {{
            background: linear-gradient(135deg, #ff5252, #ff1744);
            color: white;
        }}
        
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
        }}
        
        .section h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        /* KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
        }}
        
        .kpi-card {{
            background: rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }}
        
        .kpi-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .kpi-name {{
            font-size: 0.9rem;
            color: #a0a0a0;
            font-weight: 500;
        }}
        
        .kpi-excellent .kpi-value {{ color: #00e676; }}
        .kpi-good .kpi-value {{ color: #ffd600; }}
        .kpi-poor .kpi-value {{ color: #ff5252; }}
        .kpi-neutral .kpi-value {{ color: #a0a0a0; }}
        
        /* Blocks Table */
        .blocks-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        
        .blocks-table th {{
            background: rgba(0,212,255,0.2);
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid rgba(0,212,255,0.3);
        }}
        
        .blocks-table td {{
            padding: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        .blocks-table tr:hover {{
            background: rgba(255,255,255,0.03);
        }}
        
        .block-name {{
            font-weight: 500;
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .badge-success {{ background: #00c85333; color: #00e676; }}
        .badge-warning {{ background: #ffd60033; color: #ffd600; }}
        .badge-danger {{ background: #ff525233; color: #ff5252; }}
        
        /* Sufficiency */
        .sufficiency-container {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .sufficiency-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .sufficiency-percentage {{
            font-size: 3rem;
            font-weight: 700;
        }}
        
        .progress-excellent .sufficiency-percentage {{ color: #00e676; }}
        .progress-good .sufficiency-percentage {{ color: #ffd600; }}
        .progress-poor .sufficiency-percentage {{ color: #ff5252; }}
        
        .progress-bar {{
            height: 12px;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 6px;
            transition: width 1s ease;
        }}
        
        .progress-excellent .progress-fill {{ background: linear-gradient(90deg, #00c853, #00e676); }}
        .progress-good .progress-fill {{ background: linear-gradient(90deg, #ffc107, #ffd600); }}
        .progress-poor .progress-fill {{ background: linear-gradient(90deg, #ff5252, #ff1744); }}
        
        .blocks-count {{
            font-size: 1.1rem;
            color: #a0a0a0;
        }}
        
        .missing-blocks, .penalties {{
            background: rgba(255,82,82,0.1);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ff5252;
        }}
        
        /* Compliance Flags */
        .compliance-flag {{
            border-radius: 12px;
            margin-bottom: 1rem;
            overflow: hidden;
        }}
        
        .flag-header {{
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
        }}
        
        .flag-body {{
            padding: 1rem 1.5rem;
            padding-top: 0;
            color: #c0c0c0;
        }}
        
        .flag-body p {{
            margin-bottom: 0.5rem;
        }}
        
        .flag-critical {{
            background: linear-gradient(135deg, rgba(255,23,68,0.2), rgba(255,82,82,0.1));
            border: 1px solid rgba(255,82,82,0.3);
        }}
        
        .flag-warning {{
            background: linear-gradient(135deg, rgba(255,214,0,0.2), rgba(255,193,7,0.1));
            border: 1px solid rgba(255,214,0,0.3);
        }}
        
        .flag-info {{
            background: linear-gradient(135deg, rgba(0,230,118,0.2), rgba(0,200,83,0.1));
            border: 1px solid rgba(0,230,118,0.3);
        }}
        
        .no-flags {{
            background: linear-gradient(135deg, rgba(0,230,118,0.2), rgba(0,200,83,0.1));
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            font-size: 1.2rem;
            font-weight: 600;
            color: #00e676;
            border: 1px solid rgba(0,230,118,0.3);
        }}
        
        .errors-section {{
            background: rgba(255,82,82,0.1);
            border: 1px solid rgba(255,82,82,0.3);
            border-radius: 12px;
            padding: 1.5rem;
        }}
        
        .errors-section ul {{
            margin-left: 1.5rem;
            margin-top: 1rem;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #606060;
            font-size: 0.85rem;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            .header h1 {{
                font-size: 1.8rem;
            }}
            
            .kpi-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .blocks-table {{
                font-size: 0.85rem;
            }}
            
            .blocks-table th, .blocks-table td {{
                padding: 0.75rem 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>📊 Document Analysis Report</h1>
            <div class="header-meta">
                <span class="status-badge {status_class}">{status_icon} {status}</span>
                <span>📁 Batch: {batch_id}</span>
                <span>🕐 Generated: {generated_at}</span>
            </div>
        </header>
        
        <section class="section">
            <h2>📈 Key Performance Indicators</h2>
            <div class="kpi-grid">
                {kpis_html}
            </div>
        </section>
        
        <section class="section {suff_class}">
            <h2>📋 Document Sufficiency</h2>
            <div class="sufficiency-container">
                <div class="sufficiency-header">
                    <div class="sufficiency-percentage">{suff_pct:.1f}%</div>
                    <div class="blocks-count">📊 {suff.get('present_count', 0)} / {suff.get('required_count', 0)} Blocks Present</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {suff_pct}%;"></div>
                </div>
                {missing_html}
                {penalty_html}
            </div>
        </section>
        
        <section class="section">
            <h2>📦 Extracted Blocks</h2>
            <table class="blocks-table">
                <thead>
                    <tr>
                        <th>Block Name</th>
                        <th class="text-center">Present</th>
                        <th class="text-center">Confidence</th>
                        <th class="text-center">Fields</th>
                        <th class="text-center">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {blocks_html}
                </tbody>
            </table>
        </section>
        
        <section class="section">
            <h2>🚩 Compliance Flags</h2>
            {flags_html}
        </section>
        
        {errors_html}
        
        <footer class="footer">
            <p>Generated by Smart Approval AI • Educational Regulation Automation Platform</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Save to file
    if output_path is None:
        output_path = Path(__file__).parent / "report.html"
    else:
        output_path = Path(output_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return str(output_path)


def main():
    # Load test results
    results_path = Path(__file__).parent / "test_results.json"
    
    if not results_path.exists():
        print("❌ test_results.json not found. Run test_json_output.py first.")
        return
    
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Generate HTML report
    output_path = generate_html_report(data)
    print(f"✅ HTML report generated: {output_path}")
    print(f"\n🌐 Open in browser: file:///{output_path.replace(chr(92), '/')}")


if __name__ == "__main__":
    main()
