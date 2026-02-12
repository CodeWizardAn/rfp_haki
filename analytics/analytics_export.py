"""
Analytics Export
Export analytics data in various formats

Features:
- Multiple export formats (JSON, CSV, Excel, PDF)
- Customizable data selection
- Scheduled exports
- Data aggregation for export
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from io import BytesIO, StringIO
import json
import logging

logger = logging.getLogger(__name__)


class ExportFormat:
    """Supported export formats"""
    JSON = 'json'
    CSV = 'csv'
    EXCEL = 'excel'
    PDF = 'pdf'


class AnalyticsExporter:
    """
    Exports analytics data in various formats
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
    
    # ==================== Data Collection ====================
    
    def collect_rfp_data(self, session, start_date: datetime,
                        end_date: datetime) -> List[Dict[str, Any]]:
        """Collect RFP metrics data"""
        from .models import RFPMetric
        
        results = session.query(RFPMetric).filter(
            RFPMetric.timestamp >= start_date,
            RFPMetric.timestamp <= end_date
        ).order_by(RFPMetric.timestamp.desc()).all()
        
        return [
            {
                'id': r.id,
                'rfp_id': r.rfp_id,
                'stage': r.stage,
                'status': r.status,
                'duration_seconds': r.duration_seconds,
                'timestamp': r.timestamp.isoformat()
            }
            for r in results
        ]
    
    def collect_win_loss_data(self, session, start_date: datetime,
                             end_date: datetime) -> List[Dict[str, Any]]:
        """Collect win/loss data"""
        from .models import WinLossRecord
        
        results = session.query(WinLossRecord).filter(
            WinLossRecord.outcome_date >= start_date,
            WinLossRecord.outcome_date <= end_date
        ).order_by(WinLossRecord.outcome_date.desc()).all()
        
        return [
            {
                'id': r.id,
                'rfp_id': r.rfp_id,
                'outcome': r.outcome,
                'bid_amount': float(r.bid_amount) if r.bid_amount else None,
                'winning_amount': float(r.winning_amount) if r.winning_amount else None,
                'competitor': r.competitor,
                'industry': r.industry,
                'rfp_size': r.rfp_size,
                'outcome_date': r.outcome_date.isoformat()
            }
            for r in results
        ]
    
    def collect_agent_data(self, session, start_date: datetime,
                          end_date: datetime) -> List[Dict[str, Any]]:
        """Collect agent performance data"""
        from .models import AgentPerformanceMetric
        
        results = session.query(AgentPerformanceMetric).filter(
            AgentPerformanceMetric.timestamp >= start_date,
            AgentPerformanceMetric.timestamp <= end_date
        ).order_by(AgentPerformanceMetric.timestamp.desc()).all()
        
        return [
            {
                'id': r.id,
                'agent_type': r.agent_type,
                'request_id': r.request_id,
                'response_time_ms': r.response_time_ms,
                'tokens_used': r.tokens_used,
                'success': r.success,
                'error_type': r.error_type,
                'timestamp': r.timestamp.isoformat()
            }
            for r in results
        ]
    
    def collect_cost_data(self, session, start_date: datetime,
                         end_date: datetime) -> List[Dict[str, Any]]:
        """Collect cost data"""
        from .models import CostRecord
        
        results = session.query(CostRecord).filter(
            CostRecord.timestamp >= start_date,
            CostRecord.timestamp <= end_date
        ).order_by(CostRecord.timestamp.desc()).all()
        
        return [
            {
                'id': r.id,
                'category': r.category,
                'subcategory': r.subcategory,
                'amount': float(r.amount),
                'currency': r.currency,
                'rfp_id': r.rfp_id,
                'description': r.description,
                'timestamp': r.timestamp.isoformat()
            }
            for r in results
        ]
    
    def collect_system_health_data(self, session, start_date: datetime,
                                   end_date: datetime) -> List[Dict[str, Any]]:
        """Collect system health data"""
        from .models import SystemHealthMetric
        
        results = session.query(SystemHealthMetric).filter(
            SystemHealthMetric.timestamp >= start_date,
            SystemHealthMetric.timestamp <= end_date
        ).order_by(SystemHealthMetric.timestamp.desc()).all()
        
        return [
            {
                'id': r.id,
                'cpu_percent': r.cpu_percent,
                'memory_percent': r.memory_percent,
                'disk_percent': r.disk_percent,
                'active_connections': r.active_connections,
                'timestamp': r.timestamp.isoformat()
            }
            for r in results
        ]
    
    def collect_all_data(self, session, start_date: datetime,
                        end_date: datetime) -> Dict[str, List[Dict[str, Any]]]:
        """Collect all analytics data"""
        return {
            'rfp_metrics': self.collect_rfp_data(session, start_date, end_date),
            'win_loss': self.collect_win_loss_data(session, start_date, end_date),
            'agent_performance': self.collect_agent_data(session, start_date, end_date),
            'costs': self.collect_cost_data(session, start_date, end_date),
            'system_health': self.collect_system_health_data(session, start_date, end_date)
        }
    
    # ==================== Export Formats ====================
    
    def export_to_json(self, data: Union[Dict, List],
                      output_path: str = None,
                      pretty: bool = True) -> str:
        """Export data to JSON format"""
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'data': data
        }
        
        indent = 2 if pretty else None
        json_str = json.dumps(export_data, indent=indent, default=str)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def export_to_csv(self, data: List[Dict[str, Any]],
                     output_path: str = None) -> str:
        """Export data to CSV format"""
        if not data:
            return ""
        
        # Get all unique headers
        headers = set()
        for row in data:
            headers.update(row.keys())
        headers = sorted(list(headers))
        
        lines = [','.join(headers)]
        
        for row in data:
            values = []
            for header in headers:
                value = row.get(header, '')
                if value is None:
                    value = ''
                # Escape values with commas or quotes
                value = str(value).replace('"', '""')
                if ',' in value or '"' in value or '\n' in value:
                    value = f'"{value}"'
                values.append(value)
            lines.append(','.join(values))
        
        csv_str = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(csv_str)
        
        return csv_str
    
    def export_to_excel(self, data: Dict[str, List[Dict[str, Any]]],
                       output_path: str = None) -> bytes:
        """Export data to Excel format"""
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill
            from openpyxl.utils import get_column_letter
        except ImportError:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")
        
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        default_sheet = wb.active
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        for sheet_name, sheet_data in data.items():
            if not sheet_data:
                continue
            
            ws = wb.create_sheet(title=sheet_name[:31])  # Excel sheet name limit
            
            # Get headers
            headers = list(sheet_data[0].keys())
            
            # Write headers
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
            
            # Write data
            for row_idx, row_data in enumerate(sheet_data, 2):
                for col_idx, header in enumerate(headers, 1):
                    value = row_data.get(header, '')
                    ws.cell(row=row_idx, column=col_idx, value=value)
            
            # Auto-adjust column widths
            for col in range(1, len(headers) + 1):
                max_length = 0
                column_letter = get_column_letter(col)
                
                for row in ws.iter_rows(min_col=col, max_col=col):
                    for cell in row:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Remove the default sheet if we created others
        if len(wb.sheetnames) > 1 and 'Sheet' in wb.sheetnames:
            del wb['Sheet']
        
        buffer = BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()
        buffer.close()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(excel_bytes)
        
        return excel_bytes
    
    def export_to_pdf(self, data: Dict[str, Any],
                     title: str = "Analytics Export",
                     output_path: str = None) -> bytes:
        """Export data to PDF format"""
        from .report_generator import ReportGenerator
        
        generator = ReportGenerator(self.session_factory)
        return generator.generate_pdf('comprehensive', data, output_path)
    
    # ==================== High-Level Export Functions ====================
    
    def export(self, session, format: str, days: int = 30,
              data_types: List[str] = None,
              output_path: str = None) -> Union[str, bytes]:
        """
        Export analytics data
        
        Args:
            session: Database session
            format: Export format ('json', 'csv', 'excel', 'pdf')
            days: Number of days of data to export
            data_types: List of data types to include (None = all)
            output_path: Optional output file path
        
        Returns:
            Exported data as string (JSON, CSV) or bytes (Excel, PDF)
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Collect data
        all_data = self.collect_all_data(session, start_date, end_date)
        
        # Filter data types if specified
        if data_types:
            all_data = {k: v for k, v in all_data.items() if k in data_types}
        
        # Export in requested format
        if format == ExportFormat.JSON:
            return self.export_to_json(all_data, output_path)
        
        elif format == ExportFormat.CSV:
            # For CSV, combine all data into single list
            combined = []
            for data_type, records in all_data.items():
                for record in records:
                    record['data_type'] = data_type
                    combined.append(record)
            return self.export_to_csv(combined, output_path)
        
        elif format == ExportFormat.EXCEL:
            return self.export_to_excel(all_data, output_path)
        
        elif format == ExportFormat.PDF:
            return self.export_to_pdf(all_data, output_path=output_path)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_summary(self, session, format: str, days: int = 30,
                      output_path: str = None) -> Union[str, bytes]:
        """Export a summary of analytics data"""
        from .dashboard_api import DashboardAPI
        
        api = DashboardAPI(self.session_factory)
        overview = api.get_dashboard_overview(session, days)
        
        # Extract data from APIResponse
        data = overview.data if hasattr(overview, 'data') else overview
        
        if format == ExportFormat.JSON:
            return self.export_to_json(data, output_path)
        elif format == ExportFormat.PDF:
            return self.export_to_pdf(data, "Analytics Summary", output_path)
        else:
            raise ValueError(f"Summary export only supports JSON and PDF formats")
    
    # ==================== Streaming Export ====================
    
    def export_stream(self, session, format: str, days: int = 30,
                     batch_size: int = 1000):
        """
        Generator for streaming large exports
        
        Yields chunks of data for large datasets
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        from .models import RFPMetric
        
        offset = 0
        while True:
            results = session.query(RFPMetric).filter(
                RFPMetric.timestamp >= start_date,
                RFPMetric.timestamp <= end_date
            ).offset(offset).limit(batch_size).all()
            
            if not results:
                break
            
            data = [
                {
                    'id': r.id,
                    'rfp_id': r.rfp_id,
                    'stage': r.stage,
                    'status': r.status,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in results
            ]
            
            if format == ExportFormat.JSON:
                yield json.dumps(data)
            elif format == ExportFormat.CSV:
                yield self.export_to_csv(data)
            
            offset += batch_size
    
    # ==================== Scheduled Export ====================
    
    def schedule_export(self, export_config: Dict[str, Any]) -> str:
        """
        Schedule a recurring export
        
        Args:
            export_config: Configuration for the export including:
                - format: Export format
                - days: Number of days of data
                - data_types: Data types to include
                - output_path: Output path (supports date templates)
                - schedule: Cron-like schedule
        
        Returns:
            Schedule ID
        """
        from .scheduled_reports import ScheduledReportManager, ReportSchedule, ReportFrequency, ReportFormat
        import uuid
        
        schedule = ReportSchedule(
            id=str(uuid.uuid4()),
            name=export_config.get('name', 'Scheduled Export'),
            report_type='export',
            frequency=ReportFrequency[export_config.get('frequency', 'daily').upper()],
            format=ReportFormat[export_config.get('format', 'json').upper()],
            parameters={
                'days': export_config.get('days', 30),
                'data_types': export_config.get('data_types'),
                'output_path': export_config.get('output_path')
            }
        )
        
        # This would be integrated with the ScheduledReportManager
        return schedule.id


class ExportBuilder:
    """
    Builder pattern for creating exports
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self._exporter = AnalyticsExporter(session_factory)
        self._format = ExportFormat.JSON
        self._days = 30
        self._data_types = None
        self._output_path = None
        self._filters = {}
    
    def format(self, format: str) -> 'ExportBuilder':
        """Set export format"""
        self._format = format
        return self
    
    def days(self, days: int) -> 'ExportBuilder':
        """Set number of days"""
        self._days = days
        return self
    
    def include(self, *data_types: str) -> 'ExportBuilder':
        """Include specific data types"""
        self._data_types = list(data_types)
        return self
    
    def output(self, path: str) -> 'ExportBuilder':
        """Set output path"""
        self._output_path = path
        return self
    
    def filter(self, **kwargs) -> 'ExportBuilder':
        """Add filters"""
        self._filters.update(kwargs)
        return self
    
    def execute(self, session) -> Union[str, bytes]:
        """Execute the export"""
        return self._exporter.export(
            session,
            self._format,
            self._days,
            self._data_types,
            self._output_path
        )
