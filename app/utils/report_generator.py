from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os

class GraphoReportGenerator:
    def __init__(self, output_dir="uploads/reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e1b4b')  # Indigo-950
        )
        self.subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#4b5563')
        )
        self.disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            alignment=TA_CENTER,
            borderPadding=10,
            borderColor=colors.red,
            borderWidth=1
        )
        self.section_header = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#4338ca') # Indigo-700
        )
        self.body_text = ParagraphStyle(
            'BodyText',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=16,
            spaceAfter=12
        )

    def generate_basic_report(self, submission_id, user_name, analysis_data):
        """Standard/Free Report Generation"""
        filename = f"Grapho_Basic_{submission_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []

        # Header
        story.append(Paragraph("Graphotherapy Personality Snapshot", self.title_style))
        story.append(Paragraph(f"Prepared for: {user_name}", self.subtitle_style))
        story.append(Spacer(1, 20))

        # Content
        score = analysis_data.get('overall_score', 0)
        story.append(Paragraph(f"Overall Score: {score}/100", self.section_header))
        story.append(Paragraph(analysis_data.get('summary', ''), self.body_text))
        
        # Traits
        traits = analysis_data.get('traits', [])
        if traits:
            story.append(Paragraph("Trait Analysis", self.section_header))
            data = [['Trait', 'Score', 'Observation']]
            for t in traits:
                data.append([t.get('trait', '-'), f"{t.get('score', 0)}%", t.get('observation', '')])
            
            t = Table(data, colWidths=[2*inch, 1*inch, 3.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.indigo),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t)

        doc.build(story)
        return f"/{self.output_dir}/{filename}"

    def generate_level3_health_report(self, user_name, analysis_data):
        """
        Generates the 40-50 page equivalent 'Advanced Health Audit'.
        Strict handling of legal disclaimers.
        """
        filename = f"Grapho_Advanced_Health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []

        # --- PAGE 1: COVER ---
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("ADVANCED VITALITY AUDIT", self.title_style))
        story.append(Paragraph("Level 3 - Holistic Health & Structural Analysis", self.subtitle_style))
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph(f"Client: {user_name}", self.styles['Heading3']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['Heading3']))
        story.append(Spacer(1, 2*inch))
        
        story.append(Paragraph(
            "<b>STRICTLY CONFIDENTIAL</b><br/>This document contains sensitive psycho-somatic analysis intended solely for the recipient.",
            ParagraphStyle('Confidential', parent=self.styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)
        ))
        story.append(PageBreak())

        # --- PAGE 2: LEGAL DISCLAIMER & INTRO ---
        story.append(Paragraph("IMPORTANT MEDICAL DISCLAIMER", self.section_header))
        disclaimer_text = analysis_data.get('disclaimer_header', "This report is NOT a medical diagnosis.")
        story.append(Paragraph(
            f"<b>CRITICAL:</b> {disclaimer_text}<br/><br/>"
            "Graphotherapy is an indicative tool for identifying stress patterns in the nervous system. "
            "It does not replace professional medical advice, diagnosis, or treatment. "
            "Always consult a physician for physical ailments.",
            self.disclaimer_style
        ))
        story.append(Spacer(1, 30))
        
        story.append(Paragraph("The Mind-Body Connection", self.section_header))
        mb = analysis_data.get('mind_body_link', {})
        story.append(Paragraph(f"<b>Psychological Root:</b> {mb.get('psych_summary', '')}", self.body_text))
        story.append(Paragraph(f"<b>Somatic Effect:</b> {mb.get('somatic_effect', '')}", self.body_text))
        story.append(PageBreak())

        # --- PAGE 3: VITALITY GAUGE ---
        story.append(Paragraph("Vitality & Stress Map", self.section_header))
        vitality = analysis_data.get('vitality_audit', {})
        
        # Simple Visual Gauge Representation (Text-based for now)
        v_score = vitality.get('vitality_score', 0)
        color_v = colors.green if v_score > 70 else (colors.orange if v_score > 40 else colors.red)
        
        story.append(Paragraph(f"Vitality Score: <font color={color_v}>{v_score}/100</font>", self.styles['Heading2']))
        story.append(Paragraph(f"Energy Pattern: <b>{vitality.get('energy_pattern', 'Unknown')}</b>", self.body_text))
        story.append(Paragraph(f"Pressure Analysis: {vitality.get('pressure_analysis', '')}", self.body_text))
        
        stress = analysis_data.get('stress_map', {})
        areas = ", ".join(stress.get('tension_areas', []))
        story.append(Paragraph("Identified Tension Areas:", self.styles['Heading3']))
        story.append(Paragraph(areas, ParagraphStyle('RedBody', parent=self.body_text, textColor=colors.darkred)))
        story.append(Paragraph(stress.get('analysis', ''), self.body_text))
        story.append(PageBreak())

        # --- PAGE 4: SYSTEM SCAN ---
        story.append(Paragraph("The Inner Physician: Systems Check", self.section_header))
        indicators = analysis_data.get('specific_indicators', [])
        
        if indicators:
            table_data = [['System', 'Observation', 'Interpretation']]
            for item in indicators:
                table_data.append([
                    item.get('system', ''),
                    Paragraph(item.get('observation', ''), self.styles['Normal']),
                    Paragraph(item.get('interpretation', ''), self.styles['Normal'])
                ])
            
            t = Table(table_data, colWidths=[1.5*inch, 2*inch, 3*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1b4b')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(t)
        story.append(PageBreak())

        # --- PAGE 5: PRESCRIPTION ---
        story.append(Paragraph("Grapho-Therapy Prescription", self.section_header))
        story.append(Paragraph("Corrective handwriting exercises to retrain the nervous system.", self.styles['Italic']))
        story.append(Spacer(1, 20))
        
        rx_list = analysis_data.get('graphotherapy_prescription', [])
        for rx in rx_list:
            # Rx Box
            story.append(Paragraph(f"Rx: {rx.get('issue', 'General')}", self.styles['Heading3']))
            
            rx_data = [
                ["Exercise:", rx.get('exercise', '')],
                ["Instruction:", Paragraph(rx.get('instruction', ''), self.styles['Normal'])],
                ["Benefit:", Paragraph(rx.get('neuro_benefit', ''), self.styles['Normal'])]
            ]
            
            t = Table(rx_data, colWidths=[1.5*inch, 4.5*inch])
            t.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 1, colors.green),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f0fdf4')), # Green-50
                ('TEXTCOLOR', (0,0), (0,-1), colors.darkgreen),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

        # Footer
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            analysis_data.get('conclusion', 'Empower yourself through change.'), 
            ParagraphStyle('Footer', parent=self.styles['Italic'], alignment=TA_CENTER)
        ))

        doc.build(story)
        return f"/uploads/reports/{filename}"

# Singleton instance
report_generator = GraphoReportGenerator()
