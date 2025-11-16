"""PDF document generation for packing lists, invoices, and shipping labels."""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from config import Config

class DocumentGenerator:
    """Generate PDF documents for orders."""
    
    def __init__(self):
        """Initialize the document generator."""
        self.output_dir = Config.PDF_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
    def _get_output_path(self, doc_type: str, order_id: str) -> Path:
        """Get the output path for a document."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{doc_type}_{order_id}_{timestamp}.pdf"
        return self.output_dir / filename
    
    def generate_packing_list(self, order_data: Dict, items: List[Dict]) -> str:
        """Generate a packing list PDF."""
        output_path = self._get_output_path('packing_list', order_data['order_id'])
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("PACKING LIST", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Order Information
        info_style = self.styles['Normal']
        info_data = [
            ['Order ID:', order_data.get('order_id', 'N/A')],
            ['Order Date:', order_data.get('order_date', 'N/A')],
            ['Customer:', order_data.get('buyer_name', 'N/A')],
        ]
        info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Shipping Address
        story.append(Paragraph("<b>Ship To:</b>", self.styles['Heading3']))
        address = order_data.get('shipping_address', 'N/A')
        story.append(Paragraph(address.replace('\n', '<br/>'), info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Items Table
        story.append(Paragraph("<b>Items to Pack:</b>", self.styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        
        items_data = [['☐', 'SKU', 'Item Description', 'Qty', 'Location']]
        for item in items:
            items_data.append([
                '☐',
                item.get('sku', 'N/A'),
                item.get('title', 'N/A'),
                str(item.get('quantity', 0)),
                item.get('location', 'N/A')
            ])
        
        items_table = Table(items_data, colWidths=[0.4*inch, 1*inch, 3.5*inch, 0.6*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')]),
        ]))
        story.append(items_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", footer_style))
        
        doc.build(story)
        return str(output_path)
    
    def generate_invoice(self, order_data: Dict, items: List[Dict], shop_info: Dict = None) -> str:
        """Generate an invoice PDF."""
        output_path = self._get_output_path('invoice', order_data['order_id'])
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        story.append(Paragraph("INVOICE", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Shop Info (if provided)
        if shop_info:
            shop_style = self.styles['Normal']
            story.append(Paragraph(f"<b>{shop_info.get('shop_name', '')}</b>", shop_style))
            if shop_info.get('address'):
                story.append(Paragraph(shop_info['address'], shop_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Two-column layout for billing and order info
        header_data = [
            [
                Paragraph("<b>Bill To:</b><br/>" + order_data.get('buyer_name', 'N/A') + "<br/>" + 
                         order_data.get('buyer_email', 'N/A'), self.styles['Normal']),
                Paragraph(f"<b>Invoice #:</b> {order_data.get('order_id', 'N/A')}<br/>" +
                         f"<b>Date:</b> {order_data.get('order_date', 'N/A')}<br/>" +
                         f"<b>Status:</b> {order_data.get('status', 'N/A')}", self.styles['Normal'])
            ]
        ]
        header_table = Table(header_data, colWidths=[3.5*inch, 3*inch])
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Items Table
        items_data = [['Item', 'SKU', 'Qty', 'Unit Price', 'Total']]
        subtotal = 0
        for item in items:
            price = float(item.get('price', 0))
            qty = int(item.get('quantity', 0))
            total = price * qty
            subtotal += total
            items_data.append([
                item.get('title', 'N/A'),
                item.get('sku', 'N/A'),
                str(qty),
                f"${price:.2f}",
                f"${total:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 1.2*inch, 0.6*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')]),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Totals
        totals_data = [
            ['', '', '', 'Subtotal:', f"${subtotal:.2f}"],
            ['', '', '', 'Tax:', f"${0:.2f}"],
            ['', '', '', 'Shipping:', f"${0:.2f}"],
            ['', '', '', 'Total:', f"${order_data.get('total_amount', subtotal):.2f}"]
        ]
        totals_table = Table(totals_data, colWidths=[2.5*inch, 1.2*inch, 0.6*inch, 1*inch, 1*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (3, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (3, 3), (-1, 3), 12),
            ('LINEABOVE', (3, 3), (-1, 3), 2, colors.black),
            ('TOPPADDING', (3, 3), (-1, 3), 10),
        ]))
        story.append(totals_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Thank you for your business!", footer_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                              ParagraphStyle('SmallFooter', parent=footer_style, fontSize=8, textColor=colors.grey)))
        
        doc.build(story)
        return str(output_path)
    
    def generate_shipping_label(self, order_data: Dict, label_size: tuple = (4*inch, 6*inch)) -> str:
        """Generate a shipping label PDF."""
        output_path = self._get_output_path('shipping_label', order_data['order_id'])
        
        # Create document with custom size
        doc = SimpleDocTemplate(
            str(output_path), 
            pagesize=(label_size[0], label_size[1]),
            topMargin=0.2*inch,
            bottomMargin=0.2*inch,
            leftMargin=0.2*inch,
            rightMargin=0.2*inch
        )
        story = []
        
        # From Address (Shop)
        from_style = ParagraphStyle(
            'FromAddress',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10
        )
        story.append(Paragraph("<b>FROM:</b>", from_style))
        story.append(Paragraph(order_data.get('shop_name', 'Your Shop Name'), from_style))
        story.append(Paragraph(order_data.get('shop_address', 'Shop Address Here'), from_style))
        story.append(Spacer(1, 0.2*inch))
        
        # To Address
        to_style = ParagraphStyle(
            'ToAddress',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=16,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("<b>TO:</b>", to_style))
        story.append(Paragraph(order_data.get('buyer_name', 'N/A'), to_style))
        
        address_style = ParagraphStyle(
            'Address',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14
        )
        address_lines = order_data.get('shipping_address', 'N/A').split('\n')
        for line in address_lines:
            story.append(Paragraph(line, address_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Tracking Number
        if order_data.get('tracking_number'):
            tracking_style = ParagraphStyle(
                'Tracking',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER
            )
            story.append(Paragraph(f"<b>Tracking:</b> {order_data['tracking_number']}", tracking_style))
        
        # Order ID
        order_style = ParagraphStyle(
            'OrderID',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Order: {order_data.get('order_id', 'N/A')}", order_style))
        
        doc.build(story)
        return str(output_path)
