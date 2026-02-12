"""
Document Generator
Generates bid documents in PDF and Excel formats
"""

from typing import Optional, Dict, List
from datetime import datetime
from abc import ABC, abstractmethod
import json


class DocumentGenerator(ABC):
    """Abstract base for document generators"""
    
    @abstractmethod
    def generate(self, bid_data: Dict) -> bytes:
        """Generate document and return bytes"""
        pass
    
    @abstractmethod
    def save(self, bid_data: Dict, filepath: str) -> bool:
        """Save document to file"""
        pass


class PDFBidGenerator(DocumentGenerator):
    """Generates bid documents in PDF format"""
    
    def __init__(self):
        """Initialize PDF generator"""
        self.page_width = 210  # A4 width in mm
        self.page_height = 297  # A4 height in mm
    
    def generate(self, bid_data: Dict) -> bytes:
        """Generate PDF bid document
        
        Returns:
            PDF file as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
            from io import BytesIO
            
            # Create PDF
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            elements = []
            
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=12,
                alignment=TA_CENTER
            )
            elements.append(Paragraph("BID PROPOSAL", title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Header Info
            header_data = [
                ['Bid ID:', bid_data.get('bid_id', 'N/A'), 'RFP ID:', bid_data.get('rfp_id', 'N/A')],
                ['Vendor:', bid_data.get('vendor_name', 'N/A'), 'Date:', str(bid_data.get('issued_date', datetime.now()).date())],
                ['Valid Until:', str(bid_data.get('valid_until_date', 'N/A')), 'Version:', str(bid_data.get('version', 1))]
            ]
            
            header_table = Table(header_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Items Table
            items = bid_data.get('items', [])
            if items:
                items_data = [['Item', 'Description', 'Qty', 'Unit', 'Unit Price', 'Discount', 'Total']]
                
                for item in items:
                    items_data.append([
                        item.get('item_id', ''),
                        item.get('description', '')[:30],
                        str(item.get('quantity', 0)),
                        item.get('unit', ''),
                        f"₹{item.get('unit_price', 0):.2f}",
                        f"{item.get('discount_percent', 0)}%",
                        f"₹{item.get('total', 0):.2f}"
                    ])
                
                items_table = Table(items_data, colWidths=[0.8*inch, 1.8*inch, 0.6*inch, 0.6*inch, 1*inch, 0.7*inch, 1*inch])
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                elements.append(items_table)
                elements.append(Spacer(1, 0.2*inch))
            
            # Pricing Summary
            pricing_data = [
                ['Subtotal', f"₹{bid_data.get('subtotal', 0):,.2f}"],
                ['Discount', f"-₹{bid_data.get('discount_amount', 0):,.2f}"],
                ['Subtotal After Discount', f"₹{bid_data.get('subtotal_after_discount', 0):,.2f}"],
                ['Tax (18%)', f"₹{bid_data.get('tax_amount', 0):,.2f}"],
                ['Shipping', f"₹{bid_data.get('shipping_cost', 0):,.2f}"],
                ['GRAND TOTAL', f"₹{bid_data.get('total_cost', 0):,.2f}"]
            ]
            
            pricing_table = Table(pricing_data, colWidths=[3*inch, 2*inch])
            pricing_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(pricing_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Terms
            if bid_data.get('delivery_timeline'):
                elements.append(Paragraph(f"<b>Delivery Timeline:</b> {bid_data['delivery_timeline']}", styles['Normal']))
            if bid_data.get('payment_terms'):
                elements.append(Paragraph(f"<b>Payment Terms:</b> {bid_data['payment_terms']}", styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(f"<b>Status:</b> {bid_data.get('status', 'DRAFT')}", styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
            
        except ImportError:
            return b"ReportLab not installed"
    
    def save(self, bid_data: Dict, filepath: str) -> bool:
        """Save PDF to file"""
        try:
            pdf_bytes = self.generate(bid_data)
            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)
            return True
        except Exception as e:
            print(f"Error saving PDF: {e}")
            return False


class ExcelBidGenerator(DocumentGenerator):
    """Generates bid documents in Excel format"""
    
    def generate(self, bid_data: Dict) -> bytes:
        """Generate Excel bid document"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from io import BytesIO
            
            # Create workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Bid"
            
            # Set column widths
            ws.column_dimensions['A'].width = 15
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 12
            ws.column_dimensions['D'].width = 10
            ws.column_dimensions['E'].width = 15
            ws.column_dimensions['F'].width = 12
            ws.column_dimensions['G'].width = 15
            
            # Title
            ws['A1'] = 'BID PROPOSAL'
            ws['A1'].font = Font(size=16, bold=True, color='FFFFFF')
            ws['A1'].fill = PatternFill(start_color='1f4788', end_color='1f4788', fill_type='solid')
            ws.merge_cells('A1:G1')
            ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
            
            # Header info
            row = 3
            ws[f'A{row}'] = 'Bid ID'
            ws[f'B{row}'] = bid_data.get('bid_id', 'N/A')
            row += 1
            ws[f'A{row}'] = 'RFP ID'
            ws[f'B{row}'] = bid_data.get('rfp_id', 'N/A')
            row += 1
            ws[f'A{row}'] = 'Vendor'
            ws[f'B{row}'] = bid_data.get('vendor_name', 'N/A')
            row += 1
            ws[f'A{row}'] = 'Date'
            ws[f'B{row}'] = str(bid_data.get('issued_date', datetime.now()).date())
            row += 2
            
            # Items header
            header_row = row
            headers = ['Item', 'Description', 'Qty', 'Unit', 'Unit Price', 'Discount', 'Total']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col)
                cell.value = header
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill(start_color='1f4788', end_color='1f4788', fill_type='solid')
                cell.alignment = Alignment(horizontal='center')
            
            # Items
            row = header_row + 1
            for item in bid_data.get('items', []):
                ws.cell(row=row, column=1).value = item.get('item_id', '')
                ws.cell(row=row, column=2).value = item.get('description', '')
                ws.cell(row=row, column=3).value = item.get('quantity', 0)
                ws.cell(row=row, column=4).value = item.get('unit', '')
                ws.cell(row=row, column=5).value = item.get('unit_price', 0)
                ws.cell(row=row, column=6).value = f"{item.get('discount_percent', 0)}%"
                ws.cell(row=row, column=7).value = item.get('total', 0)
                row += 1
            
            # Pricing summary
            row += 1
            summary_start = row
            ws.cell(row=row, column=5).value = 'Subtotal'
            ws.cell(row=row, column=6).value = bid_data.get('subtotal', 0)
            row += 1
            ws.cell(row=row, column=5).value = 'Discount'
            ws.cell(row=row, column=6).value = bid_data.get('discount_amount', 0)
            row += 1
            ws.cell(row=row, column=5).value = 'Tax (18%)'
            ws.cell(row=row, column=6).value = bid_data.get('tax_amount', 0)
            row += 1
            ws.cell(row=row, column=5).value = 'GRAND TOTAL'
            ws.cell(row=row, column=6).value = bid_data.get('total_cost', 0)
            ws.cell(row=row, column=5).font = Font(bold=True)
            ws.cell(row=row, column=6).font = Font(bold=True)
            
            # Save to bytes
            excel_buffer = BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            return excel_buffer.getvalue()
            
        except ImportError:
            return b"openpyxl not installed"
    
    def save(self, bid_data: Dict, filepath: str) -> bool:
        """Save Excel to file"""
        try:
            excel_bytes = self.generate(bid_data)
            with open(filepath, 'wb') as f:
                f.write(excel_bytes)
            return True
        except Exception as e:
            print(f"Error saving Excel: {e}")
            return False


# Example usage
if __name__ == '__main__':
    bid_data = {
        'bid_id': 'BID_2026_001',
        'rfp_id': 'RFP_2026_001',
        'vendor_name': 'ABC Wires Ltd',
        'issued_date': datetime.now(),
        'valid_until_date': datetime(2026, 2, 28),
        'version': 1,
        'items': [
            {
                'item_id': 'ITEM_001',
                'description': '1.5 sqmm 3-core PVC Wire',
                'quantity': 1000,
                'unit': 'Meter',
                'unit_price': 15.50,
                'discount_percent': 5.0,
                'total': 14725.0
            },
            {
                'item_id': 'ITEM_002',
                'description': '2.5 sqmm 3-core PVC Wire',
                'quantity': 500,
                'unit': 'Meter',
                'unit_price': 25.75,
                'discount_percent': 0.0,
                'total': 15151.50
            }
        ],
        'subtotal': 29876.50,
        'discount_amount': 743.83,
        'subtotal_after_discount': 29132.67,
        'tax_amount': 5243.88,
        'shipping_cost': 500.00,
        'total_cost': 34876.55,
        'delivery_timeline': '15 days from order confirmation',
        'payment_terms': 'Net 30 days from invoice',
        'status': 'DRAFT'
    }
    
    # Generate PDF
    pdf_gen = PDFBidGenerator()
    pdf_gen.save(bid_data, '/tmp/bid_2026_001.pdf')
    print("✅ PDF generated: bid_2026_001.pdf")
    
    # Generate Excel
    excel_gen = ExcelBidGenerator()
    excel_gen.save(bid_data, '/tmp/bid_2026_001.xlsx')
    print("✅ Excel generated: bid_2026_001.xlsx")
