"""Service to generate PDF management reports."""

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

from src.models.asset import Asset
from src.models.transaction import Transaction
from src.models.report import Report
from src.models.llm_insights import LLMInsights

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generates PDF management reports."""

    # Highlight colors for key financial items
    HIGHLIGHT_TOP3 = colors.HexColor('#FEF3C7')  # Light yellow/gold for top 3 expenses
    HIGHLIGHT_LARGEST = colors.HexColor('#D1FAE5')  # Light green for largest income
    HIGHLIGHT_WARNING = colors.HexColor('#FEF3C7')  # Orange/amber for data quality warnings

    # Company display names
    COMPANY_NAMES = {
        'goedele': 'Vroedvrouw Goedele - Eenmanszaak',
        'meraki': 'Huis van Meraki - Maatschap',
    }

    def __init__(
        self,
        transactions: List[Transaction],
        report: Report,
        assets: List[Asset] = None,
        company: str = None,
        llm_insights: Optional[LLMInsights] = None
    ):
        self.transactions = transactions
        self.report = report
        self.assets = assets or []
        self.company = company
        self.company_display_name = self.COMPANY_NAMES.get(company, company or 'Eenmanszaak')
        self.llm_insights = llm_insights
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a365d'),
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c5282'),
        ))
        self.styles.add(ParagraphStyle(
            name='SubHeading',
            parent=self.styles['Heading2'],
            fontSize=13,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#2d3748'),
        ))
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14,
        ))
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
        ))

    def generate(self, output_path: Path) -> None:
        """Generate the PDF management report."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        story = []

        # Title
        story.append(Paragraph(
            f"Financieel Jaarverslag {self.report.fiscal_year}",
            self.styles['CustomTitle']
        ))
        story.append(Paragraph(
            self.company_display_name,
            self.styles['Heading2']
        ))
        story.append(Paragraph(
            f"Gegenereerd op: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))

        # Executive Summary
        story.extend(self._create_executive_summary())

        # Methodology
        story.extend(self._create_methodology_section())

        # Input Data
        story.extend(self._create_input_data_section())

        # Income Analysis
        story.extend(self._create_income_analysis())

        # Expense Analysis
        story.extend(self._create_expense_analysis())

        # Contractor Breakdown (if applicable)
        story.extend(self._create_contractor_breakdown())

        # Verworpen Uitgaven (Disallowed Expenses)
        story.extend(self._create_disallowed_expenses_section())

        # Aandachtspunten (Data Quality Warnings) - before conclusion
        story.extend(self._create_aandachtspunten_section())

        # Conclusion
        story.extend(self._create_conclusion())

        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated: {output_path}")

    def _create_executive_summary(self) -> List:
        """Create executive summary section."""
        elements = []
        elements.append(Paragraph("Samenvatting", self.styles['SectionHeading']))

        # Key figures table
        total_income = float(self.report.total_income)
        total_expenses = float(-self.report.total_expenses)
        profit = float(self.report.profit_loss)
        total_disallowed = float(self.report.total_disallowed) if self.report.disallowed_expenses else 0

        data = [
            ['Indicator', 'Bedrag'],
            ['Bruto-omzet', f"€ {total_income:,.2f}"],
            ['Totale kosten', f"€ {total_expenses:,.2f}"],
            ['Nettowinst', f"€ {profit:,.2f}"],
        ]
        if total_disallowed > 0:
            data.append(['Verworpen uitgaven', f"€ {total_disallowed:,.2f}"])

        table = Table(data, colWidths=[8*cm, 6*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f7fafc')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        # Use LLM-generated summary if available, otherwise use static fallback
        if self.llm_insights and self.llm_insights.summary_text:
            summary_text = self.llm_insights.summary_text
        else:
            summary_text = self._get_static_summary_text(total_income, total_expenses, profit)

        elements.append(Paragraph(summary_text.strip(), self.styles['BodyJustified']))

        # Add warning banner after summary if there are data quality issues
        elements.extend(self._create_warning_banner())

        return elements

    def _get_static_summary_text(self, total_income: float, total_expenses: float, profit: float) -> str:
        """Return static summary text when LLM is not available."""
        profit_margin = (profit / total_income * 100) if total_income > 0 else 0

        # Determine income source description
        income_source = ""
        if self.report.income_items and self.report.income_items[0].sub_items:
            sub_items = self.report.income_items[0].sub_items
            largest_sub = max(sub_items, key=lambda x: float(x.amount))
            largest_type = largest_sub.category.lower() if largest_sub else ""
            if 'therapeutisch' in largest_type and 'niet' not in largest_type:
                income_source = ", waarvan de meerderheid afkomstig is uit therapeutische prestaties (RIZIV-terugbetaling)"
            elif 'niet-therapeutisch' in largest_type:
                income_source = ", voornamelijk uit niet-therapeutische prestaties"

        # Determine result description based on profit/loss
        if profit >= 0:
            result_desc = "positief resultaat"
            profit_desc = f"nettowinst van € {profit:,.2f}"
        else:
            result_desc = "negatief resultaat"
            profit_desc = f"nettoverlies van € {abs(profit):,.2f}"

        return f"""
        Het boekjaar {self.report.fiscal_year} werd afgesloten met een {result_desc}.
        De totale omzet bedroeg € {total_income:,.2f}{income_source}. De totale beroepskosten bedroegen
        € {total_expenses:,.2f}, resulterend in een {profit_desc}.
        Dit vertegenwoordigt een winstmarge van {profit_margin:.1f}%.
        """

    def _create_methodology_section(self) -> List:
        """Create methodology section."""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("Methodologie", self.styles['SectionHeading']))

        elements.append(Paragraph("Databronnen", self.styles['SubHeading']))
        sources_text = """
        Dit rapport is opgesteld op basis van de volgende gegevensbronnen:
        """
        elements.append(Paragraph(sources_text.strip(), self.styles['BodyJustified']))

        source_items = [
            "Belfius bankafschriften (CSV-formaat) - alle verrichtingen op de beroepsrekening",
            "Mastercard afrekeningen (PDF-formaat) - gedetailleerde kredietkaartuitgaven",
            "Handmatige categorisatie uit referentie-Excel (Resultatenrekening 2025)",
        ]
        elements.append(ListFlowable(
            [ListItem(Paragraph(item, self.styles['Normal'])) for item in source_items],
            bulletType='bullet',
            leftIndent=20,
        ))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("Verwerkingsproces", self.styles['SubHeading']))
        process_text = """
        De financiele gegevens werden verwerkt via een geautomatiseerd systeem (PLV-tool)
        dat de volgende stappen doorloopt:
        """
        elements.append(Paragraph(process_text.strip(), self.styles['BodyJustified']))

        process_items = [
            "Import: Automatische inlezing van CSV-bankafschriften en PDF-creditcardoverzichten",
            "Deduplicatie: Detectie en uitsluiting van dubbele transacties en settlement-verrichtingen",
            "Categorisatie: Automatische toewijzing van categorien op basis van 204 patronenregels",
            "Validatie: Handmatige controle en correctie van niet-gecategoriseerde transacties",
            "Rapportage: Aggregatie en presentatie conform Belgische fiscale vereisten",
        ]
        elements.append(ListFlowable(
            [ListItem(Paragraph(f"<b>Stap {i+1}</b> - {item}", self.styles['Normal']))
             for i, item in enumerate(process_items)],
            bulletType='1',
            leftIndent=20,
        ))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("Categorisatieregels", self.styles['SubHeading']))
        rules_text = """
        De automatische categorisatie is gebaseerd op 204 patronenregels die werden geextraheerd
        uit historische, handmatig gecategoriseerde gegevens. Elke regel koppelt een tegenpartij
        of omschrijvingspatroon aan een specifieke kostencategorie. De regels worden toegepast
        in prioriteitsvolgorde, waarbij de eerste overeenkomst bepaalt welke categorie wordt toegewezen.
        """
        elements.append(Paragraph(rules_text.strip(), self.styles['BodyJustified']))

        elements.append(Paragraph("Belgische Fiscale Regels", self.styles['SubHeading']))
        tax_text = """
        Bepaalde uitgavencategorieen zijn slechts gedeeltelijk fiscaal aftrekbaar volgens
        de Belgische belastingwetgeving:
        """
        elements.append(Paragraph(tax_text.strip(), self.styles['BodyJustified']))

        tax_items = [
            "Restaurant: 69% aftrekbaar",
            "Onthaal (receptiekosten): 50% aftrekbaar",
            "Relatiegeschenken: 50% aftrekbaar",
        ]
        elements.append(ListFlowable(
            [ListItem(Paragraph(item, self.styles['Normal'])) for item in tax_items],
            bulletType='bullet',
            leftIndent=20,
        ))

        excluded_text = """
        Daarnaast werden de volgende transacties uitgesloten van de resultatenrekening:
        prive-opnames (overschrijvingen naar priverekening), interne stortingen,
        correctieboekingen (verkeerde rekening), en Mastercard-settlementbedragen
        (waarvan de details reeds in de PDF-overzichten zijn opgenomen).
        """
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(excluded_text.strip(), self.styles['BodyJustified']))

        return elements

    def _create_input_data_section(self) -> List:
        """Create input data overview section."""
        elements = []
        elements.append(Paragraph("Inputgegevens", self.styles['SectionHeading']))

        # Transaction statistics
        year_tx = [t for t in self.transactions if t.booking_date.year == self.report.fiscal_year]
        excluded_tx = [t for t in year_tx if t.is_excluded]
        categorized_tx = [t for t in year_tx if t.category and not t.is_excluded]

        # Identify source files by type (CSV vs PDF)
        source_files = set(t.source_file for t in year_tx if t.source_file)
        csv_files = sorted([f for f in source_files if f.lower().endswith('.csv')])
        pdf_files = sorted([f for f in source_files if f.lower().endswith('.pdf')])
        uncategorized_tx = [t for t in year_tx if not t.category and not t.is_excluded]

        elements.append(Paragraph("Transactie-overzicht", self.styles['SubHeading']))

        data = [
            ['Metriek', 'Aantal'],
            ['Totaal transacties verwerkt', str(len(year_tx))],
            ['Gecategoriseerde transacties', str(len(categorized_tx))],
            ['Niet-gecategoriseerde transacties', str(len(uncategorized_tx))],
            ['Uitgesloten transacties', str(len(excluded_tx))],
        ]

        table = Table(data, colWidths=[10*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        # Source files - separated by type
        elements.append(Paragraph("Bronbestanden", self.styles['SubHeading']))

        if csv_files:
            elements.append(Paragraph("<b>CSV Bankafschriften:</b>", self.styles['Normal']))
            for sf in csv_files:
                count = len([t for t in year_tx if t.source_file == sf])
                elements.append(Paragraph(f"  • {sf}: {count} transacties", self.styles['Normal']))
            elements.append(Spacer(1, 5))

        if pdf_files:
            elements.append(Paragraph("<b>PDF Creditcardoverzichten:</b>", self.styles['Normal']))
            for sf in pdf_files:
                count = len([t for t in year_tx if t.source_file == sf])
                elements.append(Paragraph(f"  • {sf}: {count} transacties", self.styles['Normal']))

        return elements

    def _create_income_analysis(self) -> List:
        """Create income analysis section."""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("Analyse Inkomsten", self.styles['SectionHeading']))

        total_income = float(self.report.total_income)
        elements.append(Paragraph(
            f"<b>Totale omzet: € {total_income:,.2f}</b>",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 10))

        # Breakdown
        if self.report.income_items:
            for item in self.report.income_items:
                if item.sub_items:
                    elements.append(Paragraph("Uitsplitsing naar type:", self.styles['SubHeading']))

                    # Identify the largest income sub_item
                    largest_idx = 0
                    if len(item.sub_items) > 1:
                        max_amount = max(sub.amount for sub in item.sub_items)
                        for idx, sub in enumerate(item.sub_items):
                            if sub.amount == max_amount:
                                largest_idx = idx
                                break

                    data = [['Status', 'Type', 'Bedrag', 'Percentage']]
                    for idx, sub in enumerate(item.sub_items):
                        status = 'Grootste' if idx == largest_idx else ''
                        pct = float(sub.amount) / total_income * 100 if total_income > 0 else 0
                        data.append([
                            status,
                            sub.category,
                            f"€ {float(sub.amount):,.2f}",
                            f"{pct:.1f}%"
                        ])
                    data.append(['', 'Totaal', f"€ {total_income:,.2f}", '100.0%'])

                    table = Table(data, colWidths=[1.8*cm, 5*cm, 5*cm, 3*cm])

                    # Base style commands
                    style_commands = [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#38a169')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#c6f6d5')),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#9ae6b4')),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]

                    # Apply green highlighting to largest income row
                    table_row = largest_idx + 1  # +1 for header
                    style_commands.append(('BACKGROUND', (0, table_row), (-1, table_row), self.HIGHLIGHT_LARGEST))

                    # Apply alternating colors for non-highlighted rows
                    for row_idx in range(1, len(item.sub_items) + 1):
                        if row_idx != table_row:
                            bg_color = colors.white if (row_idx % 2 == 1) else colors.HexColor('#f0fff4')
                            style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color))

                    table.setStyle(TableStyle(style_commands))
                    elements.append(table)

        elements.append(Spacer(1, 15))

        # Use LLM text if available, otherwise use static text
        if self.llm_insights and self.llm_insights.income_analysis_text:
            income_text = self.llm_insights.income_analysis_text
        else:
            income_text = self._get_static_income_text()

        elements.append(Paragraph(income_text.strip(), self.styles['BodyJustified']))

        return elements

    def _get_static_income_text(self) -> str:
        """Return static income analysis text based on income breakdown."""
        if not self.report.income_items or not self.report.income_items[0].sub_items:
            return """
            De omzet bestaat uit inkomsten die geboekt werden op basis van de bron-documenten.
            Alle inkomsten worden gerapporteerd volgens de standaard BTW-regeling.
            """

        sub_items = self.report.income_items[0].sub_items
        total_income = float(self.report.total_income)

        # Check if there's only one income type (100% of one category)
        if len(sub_items) == 1:
            item = sub_items[0]
            item_type = item.category.lower()
            if 'therapeutisch' in item_type and 'niet' not in item_type:
                return """
                De volledige omzet bestaat uit therapeutische prestaties (terugbetaald via RIZIV).
                Deze inkomsten zijn vrijgesteld van BTW conform artikel 44 van het BTW-Wetboek
                (medische en paramedische beroepen).
                """
            else:
                return """
                De volledige omzet bestaat uit niet-therapeutische prestaties die rechtstreeks worden
                gefactureerd. Deze diensten zijn onderworpen aan de normale BTW-regeling.
                """

        # Multiple income types - find the largest
        largest_sub = max(sub_items, key=lambda x: float(x.amount))
        largest_type = largest_sub.category.lower() if largest_sub else None

        if largest_type and 'therapeutisch' in largest_type and 'niet' not in largest_type:
            return """
            De omzet bestaat uit twee componenten: therapeutische prestaties (terugbetaald via RIZIV)
            en niet-therapeutische prestaties (rechtstreeks gefactureerd). Het therapeutische aandeel
            vormt het grootste deel van de inkomsten en is vrijgesteld van BTW conform artikel 44
            van het BTW-Wetboek (medische en paramedische beroepen).
            """
        elif largest_type and 'niet-therapeutisch' in largest_type:
            return """
            De omzet bestaat uit twee componenten: therapeutische prestaties (terugbetaald via RIZIV)
            en niet-therapeutische prestaties (rechtstreeks gefactureerd). Het niet-therapeutische aandeel
            vormt het grootste deel van de inkomsten. Dit betreft diensten die rechtstreeks worden
            gefactureerd en onderworpen zijn aan de normale BTW-regeling.
            """
        else:
            return """
            De omzet bestaat uit inkomsten die geboekt werden op basis van de bron-documenten.
            Alle inkomsten worden gerapporteerd volgens de standaard BTW-regeling.
            """

    def _create_expense_analysis(self) -> List:
        """Create expense analysis section."""
        from decimal import Decimal
        from src.services.depreciation import get_depreciation_for_year

        elements = []
        elements.append(Paragraph("Analyse Kosten en Afschrijvingen", self.styles['SectionHeading']))

        # Calculate totals separately
        total_kosten = sum(float(-item.amount) for item in self.report.expense_items)
        total_afschrijvingen = sum(float(-item.amount) for item in self.report.depreciation_items)
        total_all = total_kosten + total_afschrijvingen

        elements.append(Paragraph(
            f"<b>Totale kosten en afschrijvingen: € {total_all:,.2f}</b>",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 10))

        # KOSTEN section (operational expenses)
        if self.report.expense_items:
            elements.append(Paragraph("Kosten", self.styles['SubHeading']))
            elements.append(Paragraph(
                "Kosten zijn uitgaven die direct als beroepskost worden geboekt in het jaar van betaling.",
                self.styles['BodyJustified']
            ))
            elements.append(Spacer(1, 5))

            expense_items = sorted(self.report.expense_items, key=lambda x: float(-x.amount), reverse=True)
            data = [['Status', 'Categorie', 'Bedrag', '%']]
            for i, item in enumerate(expense_items):
                status = 'Top 3' if i < 3 else ''
                amount = float(-item.amount)
                pct = (amount / total_kosten * 100) if total_kosten > 0 else 0
                data.append([
                    status,
                    item.category.replace('-', ' ').title(),
                    f"€ {amount:,.2f}",
                    f"{pct:.1f}%"
                ])
            data.append(['', 'Totaal Kosten', f"€ {total_kosten:,.2f}", '100.0%'])

            table = Table(data, colWidths=[1.5*cm, 6.5*cm, 4*cm, 2*cm])

            # Base style commands
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c53030')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fed7d7')),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#feb2b2')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]

            # Apply yellow/gold highlighting to top 3 expense rows
            num_highlight = min(3, len(expense_items))
            for row in range(1, num_highlight + 1):
                style_commands.append(('BACKGROUND', (0, row), (-1, row), self.HIGHLIGHT_TOP3))

            # Apply alternating row colors for non-highlighted rows (after top 3, before total)
            if len(expense_items) > 3:
                style_commands.append(('ROWBACKGROUNDS', (0, 4), (-1, -2), [colors.white, colors.HexColor('#fff5f5')]))

            table.setStyle(TableStyle(style_commands))
            elements.append(table)
            elements.append(Spacer(1, 15))

        # AFSCHRIJVINGEN section (depreciation)
        if self.report.depreciation_items and self.assets:
            elements.append(Paragraph("Afschrijvingen", self.styles['SubHeading']))
            elements.append(Paragraph(
                "Afschrijvingen zijn de jaarlijkse waardevermindering van activa die op de balans staan. "
                "De aanschafwaarde wordt gespreid over de gebruiksduur van het actief.",
                self.styles['BodyJustified']
            ))
            elements.append(Spacer(1, 5))

            # Get detailed depreciation entries with asset names
            depreciation_entries = get_depreciation_for_year(self.assets, self.report.fiscal_year)

            data = [['Actief', 'Aanschafwaarde', 'Jaren', 'Afschrijving']]
            for entry in depreciation_entries:
                # Find the asset name
                asset_name = entry.asset_id
                purchase_amount = 0
                dep_years = 0
                for asset in self.assets:
                    if asset.id == entry.asset_id:
                        asset_name = asset.name
                        purchase_amount = float(asset.purchase_amount)
                        dep_years = asset.depreciation_years
                        break
                data.append([
                    asset_name,
                    f"€ {purchase_amount:,.2f}",
                    str(dep_years),
                    f"€ {float(entry.amount):,.2f}"
                ])
            data.append(['Totaal Afschrijvingen', '', '', f"€ {total_afschrijvingen:,.2f}"])

            table = Table(data, colWidths=[6*cm, 3.5*cm, 1.5*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6b46c1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9d8fd')),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#b794f4')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#faf5ff')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(table)

        # Add expense analysis text (LLM or static)
        elements.append(Spacer(1, 15))
        if self.llm_insights and self.llm_insights.expense_analysis_text:
            expense_text = self.llm_insights.expense_analysis_text
        else:
            expense_text = self._get_static_expense_text()
        elements.append(Paragraph(expense_text.strip(), self.styles['BodyJustified']))

        return elements

    def _get_static_expense_text(self) -> str:
        """Return static expense analysis text."""
        total_kosten = sum(float(-item.amount) for item in self.report.expense_items)
        total_afschrijvingen = sum(float(-item.amount) for item in self.report.depreciation_items)
        total_all = total_kosten + total_afschrijvingen

        # Find top 3 expense categories
        expense_items = sorted(self.report.expense_items, key=lambda x: float(-x.amount), reverse=True)
        top_categories = [item.category.replace('-', ' ').title() for item in expense_items[:3]]
        top_str = ', '.join(top_categories) if top_categories else 'diverse categorieën'

        return f"""
        De totale beroepskosten en afschrijvingen bedragen € {total_all:,.2f}. De voornaamste
        kostencategorieën zijn {top_str}. De spreiding van kosten over diverse categorieën
        wijst op een gevarieerd kostenpatroon typisch voor een zelfstandige praktijk.
        """

    def _create_contractor_breakdown(self) -> List:
        """Create contractor breakdown section showing commission vs payments per entity."""
        elements = []

        # Find all contractor transactions for the fiscal year
        year_tx = [t for t in self.transactions
                   if t.booking_date.year == self.report.fiscal_year
                   and t.category == 'contractors']

        if not year_tx:
            return elements

        elements.append(Paragraph("Analyse Contractors", self.styles['SectionHeading']))

        intro_text = """
        Onderstaand overzicht toont de financiële relatie met contractors (onderaannemers en
        dienstverleners). Dezelfde IBAN wordt als dezelfde entiteit beschouwd. Commissie-inkomsten
        zijn bedragen ontvangen van contractors, betalingen zijn vergoedingen aan contractors.
        """
        elements.append(Paragraph(intro_text.strip(), self.styles['BodyJustified']))
        elements.append(Spacer(1, 10))

        # Group by IBAN to identify same entities
        # For transactions without IBAN, group by counterparty name
        entity_data = {}  # key: IBAN or name, value: {names: set, commission: Decimal, payments: Decimal}

        for tx in year_tx:
            # Use IBAN as key if available, otherwise use name
            key = tx.counterparty_iban if tx.counterparty_iban else tx.counterparty_name
            if not key:
                key = 'Onbekend'

            if key not in entity_data:
                entity_data[key] = {
                    'names': set(),
                    'commission': Decimal('0'),
                    'payments': Decimal('0'),
                    'iban': tx.counterparty_iban,
                }

            if tx.counterparty_name:
                entity_data[key]['names'].add(tx.counterparty_name)

            if tx.amount > 0:
                entity_data[key]['commission'] += tx.amount
            else:
                entity_data[key]['payments'] += tx.amount  # Already negative

        # Create display data with merged entity names
        display_data = []
        for key, data in entity_data.items():
            # Create a display name from all names associated with this IBAN
            names = sorted(data['names'])
            if len(names) > 1:
                # Multiple names for same IBAN - show primary + note
                display_name = f"{names[0]} (+ {len(names)-1} alias)"
            elif names:
                display_name = names[0]
            else:
                display_name = key

            display_data.append({
                'name': display_name,
                'commission': float(data['commission']),
                'payments': float(-data['payments']),  # Make positive for display
                'net': float(data['commission'] + data['payments']),
            })

        # Sort by absolute net value (largest impact first)
        display_data.sort(key=lambda x: abs(x['net']), reverse=True)

        # Calculate totals
        total_commission = sum(d['commission'] for d in display_data)
        total_payments = sum(d['payments'] for d in display_data)
        total_net = sum(d['net'] for d in display_data)

        # Create table
        data = [['Entiteit', 'Commissie ontvangen', 'Betalingen', 'Netto']]
        for d in display_data:
            # Format net with color indicator
            net_str = f"€ {d['net']:,.2f}"
            data.append([
                d['name'][:40],  # Truncate long names
                f"€ {d['commission']:,.2f}" if d['commission'] > 0 else '-',
                f"€ {d['payments']:,.2f}" if d['payments'] > 0 else '-',
                net_str,
            ])
        data.append([
            'Totaal',
            f"€ {total_commission:,.2f}",
            f"€ {total_payments:,.2f}",
            f"€ {total_net:,.2f}",
        ])

        table = Table(data, colWidths=[5.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])

        # Determine row colors based on net value
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#bee3f8')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#90cdf4')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Color-code net column based on positive/negative
        for row_idx, d in enumerate(display_data, start=1):
            if d['net'] > 0:
                style_commands.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#276749')))
            elif d['net'] < 0:
                style_commands.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#c53030')))

        # Total row net color
        if total_net > 0:
            style_commands.append(('TEXTCOLOR', (3, -1), (3, -1), colors.HexColor('#276749')))
        elif total_net < 0:
            style_commands.append(('TEXTCOLOR', (3, -1), (3, -1), colors.HexColor('#c53030')))

        # Alternating row backgrounds
        style_commands.append(('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#ebf8ff')]))

        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 15))

        # Summary text
        if total_net > 0:
            summary = f"Het netto resultaat van contractorrelaties is positief: € {total_net:,.2f} (meer commissie ontvangen dan betaald)."
        else:
            summary = f"Het netto resultaat van contractorrelaties is negatief: € {total_net:,.2f} (meer betaald dan commissie ontvangen)."

        elements.append(Paragraph(summary, self.styles['BodyJustified']))

        return elements

    def _create_aandachtspunten_section(self) -> List:
        """Create detailed Aandachtspunten section at end of report.

        For MVP (US1): Shows uncategorized transactions with full details.
        """
        elements = []

        if not self.report.has_data_quality_warnings:
            return elements

        elements.append(PageBreak())
        elements.append(Paragraph("Aandachtspunten", self.styles['SectionHeading']))

        intro_text = """
        De volgende punten vereisen aandacht voordat het rapport definitief is.
        Controleer en corrigeer deze items om de kwaliteit van de financiële rapportage te waarborgen.
        """
        elements.append(Paragraph(intro_text.strip(), self.styles['BodyJustified']))
        elements.append(Spacer(1, 15))

        # Uncategorized transactions section (US1)
        if self.report.total_uncategorized != 0:
            count = len(self.report.uncategorized_items)
            total = float(self.report.total_uncategorized)

            elements.append(Paragraph(
                f"Niet-gecategoriseerde transacties ({count} items, totaal € {total:,.2f})",
                self.styles['SubHeading']
            ))
            elements.extend(self._create_uncategorized_table())
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                "<b>Actie vereist:</b> Controleer en categoriseer deze transacties om de volledigheid "
                "van de resultatenrekening te waarborgen.",
                self.styles['BodyJustified']
            ))
            elements.append(Spacer(1, 15))

        # Verkeerde-rekening section (US2)
        if self.report.verkeerde_rekening_balance != 0:
            count = len(self.report.verkeerde_rekening_items)
            balance = float(self.report.verkeerde_rekening_balance)
            sign = "+" if balance > 0 else ""

            elements.append(Paragraph(
                f"Privé-uitgaven (verkeerde rekening) - Niet in balans (€ {sign}{balance:,.2f})",
                self.styles['SubHeading']
            ))
            elements.extend(self._create_verkeerde_rekening_table())
            elements.append(Spacer(1, 10))

            # Different action text based on positive or negative balance
            if balance < 0:
                action_text = (
                    "<b>Actie vereist:</b> Voeg ontbrekende terugbetalingen toe of corrigeer de categorisatie. "
                    "Het negatieve saldo geeft aan dat er privé-uitgaven zijn die nog niet zijn terugbetaald."
                )
            else:
                action_text = (
                    "<b>Actie vereist:</b> Controleer of alle terugbetalingen correct zijn gecategoriseerd. "
                    "Het positieve saldo geeft aan dat er meer is terugbetaald dan er privé-uitgaven waren."
                )

            elements.append(Paragraph(action_text, self.styles['BodyJustified']))
            elements.append(Spacer(1, 15))

        return elements

    def _create_verkeerde_rekening_table(self) -> List:
        """Create a table listing verkeerde-rekening transactions.

        Uses the transactions list (not report items) for detailed info.
        """
        elements = []

        # Filter for verkeerde-rekening transactions in fiscal year
        verkeerde_tx = [
            t for t in self.transactions
            if t.booking_date.year == self.report.fiscal_year
            and t.category == 'verkeerde-rekening'
            and not t.is_excluded
        ]

        if not verkeerde_tx:
            return elements

        # Sort by date
        verkeerde_tx.sort(key=lambda t: t.booking_date)

        # Create table with transaction details
        data = [['Datum', 'Bedrag', 'Tegenpartij', 'Omschrijving']]
        for tx in verkeerde_tx:
            # Truncate description if too long
            desc = tx.description[:50] + '...' if tx.description and len(tx.description) > 50 else (tx.description or '-')
            counterparty = tx.counterparty_name[:30] + '...' if tx.counterparty_name and len(tx.counterparty_name) > 30 else (tx.counterparty_name or '-')

            data.append([
                tx.booking_date.strftime('%d/%m/%Y'),
                f"€ {float(tx.amount):,.2f}",
                counterparty,
                desc,
            ])

        table = Table(data, colWidths=[2.5*cm, 2.5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),  # Purple header for verkeerde-rekening
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a78bfa')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ede9fe')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        return elements

    def _create_uncategorized_table(self) -> List:
        """Create a table listing uncategorized transactions.

        Uses the transactions list (not report items) for detailed info.
        """
        elements = []

        # Filter for uncategorized transactions in fiscal year
        uncategorized_tx = [
            t for t in self.transactions
            if t.booking_date.year == self.report.fiscal_year
            and not t.category
            and not t.is_excluded
        ]

        if not uncategorized_tx:
            return elements

        # Sort by date
        uncategorized_tx.sort(key=lambda t: t.booking_date)

        # Create table with transaction details
        data = [['Datum', 'Bedrag', 'Tegenpartij', 'Omschrijving']]
        for tx in uncategorized_tx:
            # Truncate description if too long
            desc = tx.description[:50] + '...' if tx.description and len(tx.description) > 50 else (tx.description or '-')
            counterparty = tx.counterparty_name[:30] + '...' if tx.counterparty_name and len(tx.counterparty_name) > 30 else (tx.counterparty_name or '-')

            data.append([
                tx.booking_date.strftime('%d/%m/%Y'),
                f"€ {float(tx.amount):,.2f}",
                counterparty,
                desc,
            ])

        table = Table(data, colWidths=[2.5*cm, 2.5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d97706')),  # Amber header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fbbf24')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef3c7')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        return elements

    def _create_warning_banner(self) -> List:
        """Create a warning banner for data quality issues (page 1, after summary).

        For MVP (US1): Shows uncategorized transaction count and total.
        """
        elements = []

        if not self.report.has_data_quality_warnings:
            return elements

        # Build warning messages
        warnings = []

        # Uncategorized transactions warning (US1)
        if self.report.total_uncategorized != 0:
            count = len(self.report.uncategorized_items)
            total = float(self.report.total_uncategorized)
            warnings.append(f"{count} niet-gecategoriseerde transactie{'s' if count != 1 else ''} (€ {total:,.2f})")

        # Verkeerde-rekening balance warning (US2)
        if self.report.verkeerde_rekening_balance != 0:
            balance = float(self.report.verkeerde_rekening_balance)
            sign = "+" if balance > 0 else ""
            warnings.append(f"Verkeerde rekening niet in balans (€ {sign}{balance:,.2f})")

        if not warnings:
            return elements

        # Create the warning banner
        warning_text = "⚠ AANDACHTSPUNTEN: " + " • ".join(warnings)

        # Create a table for the warning banner with background color
        banner_data = [[warning_text]]
        banner = Table(banner_data, colWidths=[14*cm])
        banner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.HIGHLIGHT_WARNING),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#92400e')),  # Dark amber text
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d97706')),  # Amber border
        ]))

        elements.append(Spacer(1, 10))
        elements.append(banner)
        elements.append(Spacer(1, 10))

        return elements

    def _create_disallowed_expenses_section(self) -> List:
        """Create disallowed expenses (verworpen uitgaven) section."""
        elements = []

        if not self.report.disallowed_expenses:
            return elements

        elements.append(Paragraph("Verworpen Uitgaven", self.styles['SectionHeading']))

        intro_text = """
        Bepaalde beroepskosten zijn volgens de Belgische belastingwetgeving slechts gedeeltelijk
        fiscaal aftrekbaar. Het niet-aftrekbare gedeelte wordt aangeduid als 'verworpen uitgaven'
        en dient bij de belastingaangifte als disallowed expenses gerapporteerd te worden.
        """
        elements.append(Paragraph(intro_text.strip(), self.styles['BodyJustified']))
        elements.append(Spacer(1, 10))

        # Create table of disallowed expenses
        data = [['Categorie', 'Totaal bedrag', '% Aftrekbaar', 'Aftrekbaar', 'Verworpen']]
        for item in sorted(self.report.disallowed_expenses, key=lambda x: x.category):
            data.append([
                item.category,
                f"€ {float(item.total_amount):,.2f}",
                f"{item.deductible_pct}%",
                f"€ {float(item.deductible_amount):,.2f}",
                f"€ {float(item.disallowed_amount):,.2f}",
            ])

        total_disallowed = float(self.report.total_disallowed)
        data.append(['Totaal verworpen uitgaven', '', '', '', f"€ {total_disallowed:,.2f}"])

        table = Table(data, colWidths=[4.5*cm, 3*cm, 2.5*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#744210')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#faf089')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d69e2e')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fefcbf')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 15))

        # Explanation
        elements.append(Paragraph("Toelichting per categorie:", self.styles['SubHeading']))
        explanations = [
            "<b>Restaurant (69% aftrekbaar)</b>: Zakelijke maaltijden en restaurant kosten. "
            "31% wordt als verworpen uitgave beschouwd conform Art. 53 WIB.",
            "<b>Onthaal (50% aftrekbaar)</b>: Receptiekosten en onthaaluitgaven. "
            "50% wordt verworpen conform de Belgische fiscale wetgeving.",
            "<b>Relatiegeschenken (50% aftrekbaar)</b>: Geschenken aan zakelijke relaties. "
            "50% wordt verworpen conform Art. 53 WIB.",
        ]
        for exp in explanations:
            elements.append(Paragraph(f"• {exp}", self.styles['Normal']))
            elements.append(Spacer(1, 5))

        elements.append(Spacer(1, 10))
        impact_text = f"""
        <b>Impact op belastbare basis:</b> Het totaal aan verworpen uitgaven (€ {total_disallowed:,.2f})
        dient bij de jaarlijkse belastingaangifte te worden toegevoegd aan de belastbare winst.
        Dit verhoogt de effectieve belastingdruk op deze specifieke uitgavencategorieen.
        """
        elements.append(Paragraph(impact_text.strip(), self.styles['BodyJustified']))

        return elements

    def _create_conclusion(self) -> List:
        """Create conclusion section."""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("Conclusie", self.styles['SectionHeading']))

        # Use LLM-generated conclusion intro if available, otherwise use static fallback
        if self.llm_insights and self.llm_insights.conclusion_intro_text:
            conclusion_text = self.llm_insights.conclusion_intro_text
        else:
            conclusion_text = self._get_static_conclusion_text()

        elements.append(Paragraph(conclusion_text.strip(), self.styles['BodyJustified']))
        elements.append(Spacer(1, 10))

        # Key observations - use LLM insights if available
        elements.append(Paragraph("Belangrijke vaststellingen:", self.styles['SubHeading']))
        if self.llm_insights and self.llm_insights.conclusion_observations:
            observations = self.llm_insights.conclusion_observations
        else:
            observations = self._get_static_observations()
        elements.append(ListFlowable(
            [ListItem(Paragraph(obs, self.styles['Normal'])) for obs in observations],
            bulletType='bullet',
            leftIndent=20,
        ))
        elements.append(Spacer(1, 15))

        # Recommendations - use LLM insights if available
        elements.append(Paragraph("Aanbevelingen:", self.styles['SubHeading']))
        if self.llm_insights and self.llm_insights.recommendations:
            recommendations = self.llm_insights.recommendations
        else:
            recommendations = self._get_static_recommendations()
        elements.append(ListFlowable(
            [ListItem(Paragraph(rec, self.styles['Normal'])) for rec in recommendations],
            bulletType='bullet',
            leftIndent=20,
        ))

        # Signature block
        elements.append(Spacer(1, 40))
        elements.append(Paragraph("_" * 40, self.styles['Normal']))
        elements.append(Paragraph(
            f"Datum: {datetime.now().strftime('%d/%m/%Y')}",
            self.styles['Normal']
        ))

        return elements

    def _get_static_observations(self) -> List[str]:
        """Return static observations for the conclusion section."""
        total_income = float(self.report.total_income)
        total_expenses = float(-self.report.total_expenses)
        profit = float(self.report.profit_loss)
        profit_margin = (profit / total_income * 100) if total_income > 0 else 0
        total_disallowed = float(self.report.total_disallowed) if self.report.disallowed_expenses else 0

        # Determine income type for observation
        income_source_text = ""
        if self.report.income_items and self.report.income_items[0].sub_items:
            sub_items = self.report.income_items[0].sub_items
            largest_sub = max(sub_items, key=lambda x: float(x.amount))
            largest_type = largest_sub.category.lower() if largest_sub else ""
            if 'therapeutisch' in largest_type and 'niet' not in largest_type:
                income_source_text = ", voornamelijk uit therapeutische prestaties (RIZIV)"
            elif 'niet-therapeutisch' in largest_type:
                income_source_text = ", voornamelijk uit niet-therapeutische prestaties"

        observations = [
            f"De praktijk genereerde € {total_income:,.2f} aan omzet{income_source_text}",
            f"De winstmarge van {profit_margin:.1f}% toont een gezonde financiele situatie",
            "Alle transacties werden succesvol gecategoriseerd volgens de Belgische fiscale vereisten",
            "De automatische categorisatie verzekert consistentie in de boekhouding",
        ]
        if total_disallowed > 0:
            observations.append(f"Verworpen uitgaven bedragen € {total_disallowed:,.2f} (te rapporteren bij belastingaangifte)")

        return observations

    def _get_static_recommendations(self) -> List[str]:
        """Return static recommendations for the conclusion section."""
        return [
            "Behoud de huidige structuur voor financiele administratie",
            "Overweeg periodieke controle van categorisatieregels om nieuwe leveranciers op te nemen",
            "Bewaar bronbestanden (CSV/PDF) conform de wettelijke bewaartermijn van 7 jaar",
        ]

    def _get_static_conclusion_text(self) -> str:
        """Return static conclusion intro text when LLM is not available."""
        total_income = float(self.report.total_income)
        total_expenses = float(-self.report.total_expenses)
        profit = float(self.report.profit_loss)
        profit_margin = (profit / total_income * 100) if total_income > 0 else 0

        # Determine assessment based on profit/loss
        if profit >= 0:
            assessment = "kan als succesvol worden beschouwd"
            result_phrase = f"werd een nettowinst van € {profit:,.2f} gerealiseerd"
        else:
            assessment = "werd afgesloten met een verlies"
            result_phrase = f"werd een nettoverlies van € {abs(profit):,.2f} gerealiseerd"

        return f"""
        Het boekjaar {self.report.fiscal_year} {assessment}.
        Met een totale omzet van € {total_income:,.2f} en beroepskosten van € {total_expenses:,.2f}
        {result_phrase}, wat neerkomt op een winstmarge
        van {profit_margin:.1f}%.
        """


def generate_management_report(
    transactions: List[Transaction],
    report: Report,
    output_path: Path,
    assets: List[Asset] = None,
    company: str = None,
    llm_insights: Optional[LLMInsights] = None
) -> None:
    """Generate a PDF management report.

    Args:
        transactions: List of all transactions
        report: P&L report object
        output_path: Path for the output PDF file
        assets: List of assets for depreciation details
        company: Company name for customizing the report title
        llm_insights: Optional AI-generated insights for dynamic text
    """
    generator = PDFReportGenerator(transactions, report, assets, company, llm_insights)
    generator.generate(output_path)
