"""
PDF Report Generator - SQLite version
Minimal, official format
"""

import os
import logging
from typing import Dict, Any, List
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Template
from config.database import get_db, Batch, Block, ComplianceFlag, close_db
from config.settings import settings
from config.information_blocks import get_information_blocks, get_block_description
from datetime import datetime

logger = logging.getLogger(__name__)

# WeasyPrint is optional; if unavailable or misconfigured, we fall back to HTML output
try:
    from weasyprint import HTML  # type: ignore
except Exception as weasy_err:  # ImportError or environment errors
    logger.warning(f"WeasyPrint not fully available, will use HTML-only reports. Error: {weasy_err}")
    HTML = None

class ReportGenerator:
    def __init__(self):
        self.template_dir = Path("templates")
        self.template_dir.mkdir(exist_ok=True)
    
    def generate_report(
        self,
        batch_id: str,
        include_evidence: bool = True,
        include_trends: bool = True,
        report_type: str = "standard"
    ) -> str:
        """Generate PDF report for batch"""
        db = get_db()
        
        try:
            batch = db.query(Batch).filter(Batch.id == batch_id).first()
            if not batch:
                raise ValueError(f"Batch {batch_id} not found")
            
            # Get information blocks
            blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
            
            # Render HTML template
            html_content = self._render_template(
                batch,
                blocks,
                include_evidence,
                include_trends,
                report_type
            )
            
            # Generate PDF (with HTML fallback if PDF or WeasyPrint is unavailable)
            os.makedirs(settings.REPORTS_DIR, exist_ok=True)
            pdf_path = os.path.join(settings.REPORTS_DIR, f"report_{batch_id}.pdf")
            
            if HTML is None:
                # Environment cannot support WeasyPrint – save HTML directly
                logger.warning("WeasyPrint not available; saving report as HTML only.")
                html_path = pdf_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return html_path

            try:
                HTML(string=html_content).write_pdf(pdf_path)
            except Exception as pdf_error:
                # Fallback: save as HTML if PDF generation fails
                logger.warning(f"PDF generation failed: {pdf_error}. Saving as HTML instead.")
                html_path = pdf_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return html_path
            
            return pdf_path
        finally:
            close_db(db)
    
    def _render_template(
        self,
        batch: Batch,
        blocks: List[Block],
        include_evidence: bool,
        include_trends: bool,
        report_type: str
    ) -> str:
        """Render HTML template"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Institutional Evaluation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #1a1a1a; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }
        h2 { color: #333; margin-top: 30px; }
        .header { margin-bottom: 30px; }
        .kpi-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; }
        .kpi-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .kpi-value { font-size: 32px; font-weight: bold; color: #0066cc; }
        .sufficiency { padding: 20px; border: 2px solid #ddd; border-radius: 5px; margin: 20px 0; }
        .compliance-flag { padding: 10px; margin: 10px 0; border-left: 4px solid #ff6b6b; }
        .compliance-flag.medium { border-left-color: #ffa500; }
        .compliance-flag.low { border-left-color: #4caf50; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; }
        .block-card { border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px; }
        .block-present { background-color: #e8f5e9; }
        .block-missing { background-color: #ffebee; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Institutional Evaluation Report</h1>
        <p><strong>Mode:</strong> {{ mode.upper() }}</p>
        <p><strong>Report Type:</strong> {{ report_type.upper() }}</p>
        <p><strong>Batch ID:</strong> {{ batch_id }}</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
    </div>

    <h2>Approval Classification</h2>
    <div class="sufficiency">
        <p><strong>Category:</strong> {{ approval_classification.category if approval_classification else "unknown" }}</p>
        <p><strong>Subtype:</strong> {{ approval_classification.subtype if approval_classification else "unknown" }}</p>
        {% if approval_classification and approval_classification.signals %}
        <p><strong>Signals:</strong> {{ ", ".join(approval_classification.signals) }}</p>
        {% endif %}
    </div>

    <h2>Approval Readiness</h2>
    <div class="sufficiency">
        {% if approval_readiness %}
        <p><strong>Readiness Score:</strong> {{ "%.2f"|format(approval_readiness.get("readiness_score", approval_readiness.get("approval_readiness_score", 0))) }}%</p>
        
        {% if approval_readiness.get("present_documents") %}
        <h3>Present Documents (Evidence Found)</h3>
        <ul>
            {% for doc in approval_readiness.present_documents %}
            <li>
                <strong>{{ doc.description or doc.key }}:</strong>
                {% if doc.evidence %}
                <span>Found (confidence: {{ "%.1f"|format(doc.evidence.confidence * 100) }}%)</span>
                {% if doc.evidence.snippet %}
                <br><em>Snippet: {{ doc.evidence.snippet[:150] }}...</em>
                {% endif %}
                {% if doc.evidence.page %}
                <br><small>Page: {{ doc.evidence.page }}</small>
                {% endif %}
                {% endif %}
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if approval_readiness.get("missing_documents") %}
        <h3>Missing Documents (Examined but Not Found)</h3>
        <ul>
            {% for doc in approval_readiness.missing_documents %}
            <li>
                <strong>{{ doc.description or doc.key }}:</strong>
                <span>{{ doc.reason or "Not found in extracted data" }}</span>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if approval_readiness.get("unknown_documents") %}
        <h3>Unknown Documents (Not Examined)</h3>
        <ul>
            {% for doc in approval_readiness.unknown_documents %}
            <li>
                <strong>{{ doc.description or doc.key }}:</strong>
                <span>{{ doc.reason or "No relevant block found in uploaded documents" }}</span>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if approval_readiness.get("recommendation") %}
        <p><strong>Recommendation:</strong> {{ approval_readiness.recommendation }}</p>
        {% endif %}
        {% else %}
        <p>No approval readiness data available.</p>
        {% endif %}
    </div>
    
    <h2>KPI Performance</h2>
    <div class="kpi-grid">
        {% for kpi_id, kpi_data in kpis.items() %}
        {% set value = kpi_data.value %}
        <div class="kpi-card">
            <h3>{{ kpi_data.name }}</h3>
            <div class="kpi-value">
                {% if value is none %}
                    Insufficient Data
                {% else %}
                    {{ "%.2f"|format(value) }}
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    
    <h2>Information Block Sufficiency</h2>
    <div class="sufficiency">
        <p><strong>Score:</strong> {{ "%.2f"|format(sufficiency.percentage) }}%</p>
        <p><strong>Present:</strong> {{ sufficiency.present_count }} / {{ sufficiency.required_count }}</p>
        {% if sufficiency.missing_blocks %}
        <p><strong>Missing Blocks:</strong> {{ ", ".join(sufficiency.missing_blocks) }}</p>
        {% endif %}
    </div>
    
    <h2>Information Blocks</h2>
    <table>
        <tr>
            <th>Block Type</th>
            <th>Status</th>
            <th>Confidence</th>
            <th>Fields Extracted</th>
            <th>Quality Flags</th>
        </tr>
        {% for block in blocks %}
        <tr>
            <td>{{ block.block_name }}</td>
            <td>{% if block.is_invalid %}Invalid{% elif block.is_outdated %}Outdated{% elif block.is_low_quality %}Low Quality{% elif block.is_present %}Valid{% else %}Missing{% endif %}</td>
            <td>{{ "%.2f"|format(block.confidence * 100) }}%</td>
            <td>{{ block.extracted_fields_count }}</td>
            <td>
                {% if block.is_outdated %}Outdated {% endif %}
                {% if block.is_low_quality %}Low Quality {% endif %}
                {% if block.is_invalid %}Invalid{% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>Compliance Flags</h2>
    {% for flag in compliance %}
    <div class="compliance-flag {{ flag.severity }}">
        <h3>{{ flag.title }}</h3>
        <p>{{ flag.reason }}</p>
        {% if flag.recommendation %}
        <p><strong>Recommendation:</strong> {{ flag.recommendation }}</p>
        {% endif %}
    </div>
    {% endfor %}
    
    {% if trends and trends.has_trend_data %}
    <h2>Performance Trends (from PDF tables)</h2>
    <p>Trend data extracted from multi-year tables in uploaded PDFs.</p>
    {% endif %}
</body>
</html>
        """
        
        # Group blocks by type and prepare for template
        new_university = bool(batch.new_university) if batch.new_university else False
        required_blocks = get_information_blocks(batch.mode, new_university)  # Get mode-specific blocks (conditional for UGC)
        blocks_by_type = {}
        for block in blocks:
            block_type = block.block_type
            if block_type:
                if block_type not in blocks_by_type:
                    blocks_by_type[block_type] = []
                blocks_by_type[block_type].append(block)
        
        # Create block summary for template
        block_summary = []
        for block_type in required_blocks:
            block_list = blocks_by_type.get(block_type, [])
            if block_list:
                best_block = max(block_list, key=lambda b: b.extraction_confidence)
                block_summary.append({
                    "block_type": block_type,
                    "block_name": get_block_description(block_type).get("name", block_type),
                    "confidence": best_block.extraction_confidence,
                    "extracted_fields_count": len(best_block.data or {}),
                    "is_outdated": bool(best_block.is_outdated),
                    "is_low_quality": bool(best_block.is_low_quality),
                    "is_invalid": bool(best_block.is_invalid),
                    "is_present": True
                })
            else:
                block_summary.append({
                    "block_type": block_type,
                    "block_name": get_block_description(block_type).get("name", block_type),
                    "confidence": 0.0,
                    "extracted_fields_count": 0,
                    "is_outdated": False,
                    "is_low_quality": False,
                    "is_invalid": False,
                    "is_present": False
                })
        
        # Normalize sufficiency to always have expected fields/types
        suff_raw = batch.sufficiency_result or {}
        if not isinstance(suff_raw, dict):
            suff_raw = {}
        missing_blocks = suff_raw.get("missing_blocks") or []
        if not isinstance(missing_blocks, list):
            missing_blocks = []
        sufficiency = SimpleNamespace(
            percentage=float(suff_raw.get("percentage", 0) or 0),
            present_count=int(suff_raw.get("present_count", 0) or 0),
            required_count=int(suff_raw.get("required_count", 0) or 0),
            missing_blocks=missing_blocks,
        )

        # Normalize KPI results into objects with name/value
        kpi_raw = batch.kpi_results or {}
        kpis: Dict[str, Any] = {}
        if isinstance(kpi_raw, dict):
            for kpi_id, kpi_data in kpi_raw.items():
                if isinstance(kpi_data, dict):
                    name = kpi_data.get("name", kpi_id.replace("_", " ").title())
                    value = kpi_data.get("value")
                else:
                    name = kpi_id.replace("_", " ").title()
                    value = kpi_data
                kpis[kpi_id] = SimpleNamespace(name=name, value=value)

        compliance = batch.compliance_results or []
        trends = batch.trend_results or {}

        # Approval classification/readiness normalisation for template safety
        approval_classification = batch.approval_classification or {}
        if not isinstance(approval_classification, dict):
            approval_classification = {}

        ar_raw = batch.approval_readiness or {}
        if not isinstance(ar_raw, dict):
            ar_raw = {}
        for key in ["present_documents", "missing_documents", "unknown_documents"]:
            val = ar_raw.get(key) or []
            if not isinstance(val, list):
                val = []
            ar_raw[key] = val
        approval_readiness = ar_raw
        
        template = Template(template_str)
        
        return template.render(
            mode=batch.mode,
            batch_id=batch.id,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            kpis=kpis,
            sufficiency=sufficiency,
            compliance=compliance,
            blocks=block_summary,
            trends=trends,
            approval_classification=approval_classification,
            approval_readiness=approval_readiness,
            report_type=report_type,
        )
