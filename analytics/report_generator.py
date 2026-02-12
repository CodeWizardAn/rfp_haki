"""
Report Generator
Generates comprehensive PDF and Excel reports

Features:
- PDF report generation
- Excel report generation
- Customizable templates
- Charts and visualizations
- Automated scheduling
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from io import BytesIO
import json
import logging

logger = logging.getLogger(__name__)

# Try importing optional dependencies
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class ReportGenerator:
    """
    Generates comprehensive analytics reports in PDF and Excel formats
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        
        # Report templates
        self._templates = {
            'executive_summary': self._generate_executive_summary,
            'detailed_analytics': self._generate_detailed_analytics,
            'rfp_performance': self._generate_rfp_performance,
            'agent_performance': self._generate_agent_performance,
            'cost_analysis': self._generate_cost_analysis,
            'win_loss': self._generate_win_loss_report
        }
    
    def get_available_templates(self) -> List[str]:
        """Get list of available report templates"""
        return list(self._templates.keys())
    
    # ==================== PDF Generation ====================
    
    def generate_pdf(self, report_type: str, data: Dict[str, Any],
                    output_path: str = None) -> bytes:
        """Generate a PDF report"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        # Get styles
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Analytics Report: {report_type.replace('_', ' ').title()}", title_style))
        story.append(Spacer(1, 12))
        
        # Add generation date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", date_style))
        story.append(Spacer(1, 30))
        
        # Generate report content based on type
        if report_type in self._templates:
            self._templates[report_type](story, data, styles)
        else:
            self._generate_generic_report(story, data, styles)
        
        # Build PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def _add_section_header(self, story: List, title: str, styles):
        """Add a section header to the report"""
        header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20
        )
        story.append(Paragraph(title, header_style))
    
    def _add_key_metrics_table(self, story: List, metrics: Dict[str, Any], styles):
        """Add a key metrics table"""
        data = [['Metric', 'Value']]
        for key, value in metrics.items():
            if isinstance(value, float):
                value = f"{value:.2f}"
            data.append([key.replace('_', ' ').title(), str(value)])
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D6DCE4')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
    
    def _generate_executive_summary(self, story: List, data: Dict[str, Any], styles):
        """Generate executive summary report"""
        self._add_section_header(story, "Executive Summary", styles)
        
        # Key metrics
        if 'summary' in data:
            self._add_key_metrics_table(story, data['summary'], styles)
        
        # Highlights
        if 'highlights' in data:
            self._add_section_header(story, "Key Highlights", styles)
            for highlight in data['highlights']:
                story.append(Paragraph(f"• {highlight}", styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Recommendations
        if 'recommendations' in data:
            self._add_section_header(story, "Recommendations", styles)
            for rec in data['recommendations']:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
                story.append(Spacer(1, 6))
    
    def _generate_detailed_analytics(self, story: List, data: Dict[str, Any], styles):
        """Generate detailed analytics report"""
        for section, content in data.items():
            self._add_section_header(story, section.replace('_', ' ').title(), styles)
            
            if isinstance(content, dict):
                self._add_key_metrics_table(story, content, styles)
            elif isinstance(content, list):
                self._add_list_as_table(story, content)
    
    def _generate_rfp_performance(self, story: List, data: Dict[str, Any], styles):
        """Generate RFP performance report"""
        self._add_section_header(story, "RFP Processing Performance", styles)
        
        if 'processing_stats' in data:
            self._add_key_metrics_table(story, data['processing_stats'], styles)
        
        if 'stage_timing' in data:
            self._add_section_header(story, "Processing Stage Breakdown", styles)
            self._add_key_metrics_table(story, data['stage_timing'], styles)
    
    def _generate_agent_performance(self, story: List, data: Dict[str, Any], styles):
        """Generate agent performance report"""
        self._add_section_header(story, "Agent Performance Metrics", styles)
        
        if 'agents' in data:
            for agent_data in data['agents']:
                agent_type = agent_data.get('agent_type', 'Unknown')
                story.append(Paragraph(f"<b>{agent_type}</b>", styles['Heading3']))
                self._add_key_metrics_table(story, agent_data, styles)
    
    def _generate_cost_analysis(self, story: List, data: Dict[str, Any], styles):
        """Generate cost analysis report"""
        self._add_section_header(story, "Cost Analysis", styles)
        
        if 'summary' in data:
            self._add_key_metrics_table(story, data['summary'], styles)
        
        if 'by_category' in data:
            self._add_section_header(story, "Costs by Category", styles)
            self._add_list_as_table(story, data['by_category'])
    
    def _generate_win_loss_report(self, story: List, data: Dict[str, Any], styles):
        """Generate win/loss analysis report"""
        self._add_section_header(story, "Win/Loss Analysis", styles)
        
        if 'overall' in data:
            self._add_key_metrics_table(story, data['overall'], styles)
        
        if 'by_segment' in data:
            self._add_section_header(story, "Performance by Segment", styles)
            self._add_list_as_table(story, data['by_segment'])
    
    def _generate_generic_report(self, story: List, data: Dict[str, Any], styles):
        """Generate a generic report from data"""
        for key, value in data.items():
            self._add_section_header(story, key.replace('_', ' ').title(), styles)
            
            if isinstance(value, dict):
                self._add_key_metrics_table(story, value, styles)
            elif isinstance(value, list) and value:
                self._add_list_as_table(story, value)
            else:
                story.append(Paragraph(str(value), styles['Normal']))
                story.append(Spacer(1, 12))
    
    def _add_list_as_table(self, story: List, data: List[Dict[str, Any]]):
        """Convert a list of dicts to a table"""
        if not data:
            return
        
        headers = list(data[0].keys())
        table_data = [headers]
        
        for item in data:
            row = []
            for header in headers:
                value = item.get(header, '')
                if isinstance(value, float):
                    value = f"{value:.2f}"
                row.append(str(value))
            table_data.append(row)
        
        col_width = 6.5 * inch / len(headers)
        table = Table(table_data, colWidths=[col_width] * len(headers))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')])
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
    
    # ==================== Excel Generation ====================
    
    def generate_excel(self, report_type: str, data: Dict[str, Any],
                      output_path: str = None) -> bytes:
        """Generate an Excel report"""
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl is required for Excel generation. Install with: pip install openpyxl")
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Summary"
        
        # Style definitions
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Add title
        ws['A1'] = f"Analytics Report: {report_type.replace('_', ' ').title()}"
        ws['A1'].font = Font(bold=True, size=16)
        ws.merge_cells('A1:D1')
        
        ws['A2'] = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        ws['A2'].font = Font(italic=True, color="808080")
        
        current_row = 4
        
        # Add data sections
        for section_name, section_data in data.items():
            # Section header
            ws.cell(row=current_row, column=1, value=section_name.replace('_', ' ').title())
            ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
            current_row += 1
            
            if isinstance(section_data, dict):
                # Key-value pairs
                for key, value in section_data.items():
                    if isinstance(value, (dict, list)):
                        continue
                    ws.cell(row=current_row, column=1, value=key.replace('_', ' ').title())
                    ws.cell(row=current_row, column=2, value=value)
                    current_row += 1
            
            elif isinstance(section_data, list) and section_data:
                # Create a table
                if isinstance(section_data[0], dict):
                    headers = list(section_data[0].keys())
                    
                    # Headers
                    for col, header in enumerate(headers, 1):
                        cell = ws.cell(row=current_row, column=col, value=header.replace('_', ' ').title())
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = border
                    current_row += 1
                    
                    # Data rows
                    for item in section_data:
                        for col, header in enumerate(headers, 1):
                            cell = ws.cell(row=current_row, column=col, value=item.get(header, ''))
                            cell.border = border
                        current_row += 1
            
            current_row += 1  # Empty row between sections
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to buffer
        buffer = BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()
        buffer.close()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(excel_bytes)
        
        return excel_bytes
    
    # ==================== JSON/CSV Generation ====================
    
    def generate_json(self, data: Dict[str, Any], output_path: str = None) -> str:
        """Generate a JSON report"""
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'data': data
        }
        
        json_str = json.dumps(report, indent=2, default=str)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def generate_csv(self, data: List[Dict[str, Any]], output_path: str = None) -> str:
        """Generate a CSV report from list of dicts"""
        if not data:
            return ""
        
        headers = list(data[0].keys())
        lines = [','.join(headers)]
        
        for row in data:
            values = [str(row.get(h, '')).replace(',', ';') for h in headers]
            lines.append(','.join(values))
        
        csv_str = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(csv_str)
        
        return csv_str
    
    # ==================== Combined Reports ====================
    
    def generate_comprehensive_report(self, session, 
                                      format: str = 'pdf',
                                      days: int = 30,
                                      output_path: str = None) -> bytes:
        """Generate a comprehensive analytics report"""
        from .rfp_metrics import RFPMetricsTracker
        from .win_loss_analytics import WinLossAnalytics
        from .agent_performance import AgentPerformanceTracker
        from .cost_analysis import CostAnalyzer
        from .roi_calculator import ROICalculator
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Collect data from all trackers
        rfp_tracker = RFPMetricsTracker()
        win_loss = WinLossAnalytics()
        agent_tracker = AgentPerformanceTracker()
        cost_analyzer = CostAnalyzer()
        roi_calc = ROICalculator()
        
        data = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'rfp_performance': rfp_tracker.get_performance_summary(session, days),
            'win_loss': win_loss.get_overall_win_rate(session, start_date, end_date),
            'agent_performance': agent_tracker.get_all_agents_comparison(session, start_date, end_date),
            'costs': cost_analyzer.get_total_costs(session, start_date, end_date),
            'roi': roi_calc.calculate_roi(session, start_date, end_date)
        }
        
        if format == 'pdf':
            return self.generate_pdf('comprehensive', data, output_path)
        elif format == 'excel':
            return self.generate_excel('comprehensive', data, output_path)
        elif format == 'json':
            return self.generate_json(data, output_path).encode()
        else:
            raise ValueError(f"Unsupported format: {format}")
