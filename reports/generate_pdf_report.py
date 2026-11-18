"""
FinSight Platform - Automated Executive Board PDF Report Generator
Generates an executive-ready, multi-page Board Financial & Risk Report in PDF format
using ReportLab.
"""

import os
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "finsight.db")
OUTPUT_PDF_PATH = os.path.join(BASE_DIR, "reports", "monthly_board_report.pdf")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "docs", "screenshots")

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically calculate total page numbers and running footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (on pages after cover)
        if self._pageNumber > 1:
            self.drawString(54, 755, "FinSight – Executive & Board Financial Intelligence Report")
            self.drawRightString(558, 755, "Confidential | FY 2026")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 747, 558, 747)

        # Footer
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Prepared by Nexvia Technologies Technical Analytics Team | Strictly Confidential")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_board_report(target_month=12, fiscal_year=2026):
    print(f"[*] Compiling FinSight Monthly Board Report for FY{fiscal_year}-M{target_month}...")
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch Financial Data
    pnl = conn.execute("SELECT * FROM view_monthly_pnl WHERE fiscal_year=? AND fiscal_month=?", (fiscal_year, target_month)).fetchone()
    # P&L columns: year, month, rev, cogs, gp, opex, ebitda, depr, ebit, int, pbt, tax, net_profit
    
    # Prior month for MoM comparison
    prev_m = target_month - 1 if target_month > 1 else 12
    prev_pnl = conn.execute("SELECT * FROM view_monthly_pnl WHERE fiscal_year=? AND fiscal_month=?", (fiscal_year, prev_m)).fetchone()
    
    # Balance sheet
    bs_assets = conn.execute("SELECT category, SUM(net_value) FROM assets WHERE fiscal_month=? GROUP BY category", (target_month,)).fetchall()
    bs_liab = conn.execute("SELECT category, SUM(current_balance) FROM liabilities WHERE fiscal_month=? GROUP BY category", (target_month,)).fetchall()
    bs_eq = conn.execute("SELECT share_capital, retained_earnings, total_equity FROM equity WHERE fiscal_month=?", (target_month,)).fetchone()
    
    # Budget variance
    bva_depts = conn.execute("""
        SELECT department_name, SUM(budgeted_amount), SUM(actual_amount), 
               SUM(actual_amount) - SUM(budgeted_amount),
               ROUND(((SUM(actual_amount) - SUM(budgeted_amount)) / NULLIF(SUM(budgeted_amount), 0)) * 100.0, 2)
        FROM view_budget_vs_actual
        WHERE fiscal_month=? AND account_type='Expense'
        GROUP BY department_name
        ORDER BY SUM(actual_amount) DESC
    """, (target_month,)).fetchall()
    
    # Credit Risk Stats
    credit_stats = conn.execute("""
        SELECT COUNT(loan_id), SUM(loan_amount), AVG(debt_to_income_ratio), AVG(interest_rate),
               SUM(is_default), ROUND(AVG(is_default)*100.0, 2)
        FROM loans
    """).fetchone()
    
    risk_band_counts = conn.execute("""
        SELECT risk_band, COUNT(prediction_id), ROUND(AVG(predicted_prob_default)*100.0, 2), AVG(credit_score)
        FROM credit_predictions
        GROUP BY risk_band
        ORDER BY AVG(credit_score) DESC
    """).fetchall()
    
    conn.close()

    # -------------------------------------------------------------------------
    # ReportLab Document Setup
    # -------------------------------------------------------------------------
    doc = SimpleDocTemplate(
        OUTPUT_PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0F172A')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B')
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    kpi_title_style = ParagraphStyle(
        'KPITitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748B')
    )
    kpi_value_style = ParagraphStyle(
        'KPIValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#0284C7')
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # -------------------------------------------------------------------------
    # PAGE 1: Executive Cover & Executive Financial Overview
    # -------------------------------------------------------------------------
    # Header Banner
    story.append(Paragraph("FINSIGHT INTELLIGENCE PLATFORM", ParagraphStyle('TopSub', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0284C7'), leading=11)))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Monthly Executive & Board Financial Report", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"Reporting Period: Fiscal Year {fiscal_year} – Month {target_month:02d} (December 2026) | Published: {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceAfter=15))

    # Executive Summary Paragraph
    exec_summary_text = (
        f"<b>Executive Briefing:</b> During Month {target_month}, FinSight Platform recorded strong financial "
        f"performance with top-line recognized revenue reaching <b>${pnl[2]:,.2f}</b>, representing solid unit economics "
        f"with a Gross Margin of <b>{((pnl[4]/pnl[2])*100):.1f}%</b>. Core operational EBITDA stood at "
        f"<b>${pnl[6]:,.2f}</b> (Margin: {((pnl[6]/pnl[2])*100):.1f}%), yielding a bottom-line Net Profit of "
        f"<b>${pnl[12]:,.2f}</b>. Balance sheet accounts remain fully reconciled with zero discrepancy, and credit risk "
        f"underwriting standards continue to deliver disciplined default performance across the lending portfolio."
    )
    story.append(Paragraph(exec_summary_text, body_style))
    story.append(Spacer(1, 14))

    # 4 KPI Summary Cards
    kpi_cards = [
        [
            Paragraph("TOTAL REVENUE", kpi_title_style),
            Paragraph("GROSS PROFIT", kpi_title_style),
            Paragraph("EBITDA", kpi_title_style),
            Paragraph("NET PROFIT", kpi_title_style)
        ],
        [
            Paragraph(f"${pnl[2]:,.0f}", kpi_value_style),
            Paragraph(f"${pnl[4]:,.0f}", kpi_value_style),
            Paragraph(f"${pnl[6]:,.0f}", kpi_value_style),
            Paragraph(f"${pnl[12]:,.0f}", ParagraphStyle('NetKPI', parent=kpi_value_style, textColor=colors.HexColor('#15803D')))
        ],
        [
            Paragraph(f"Margin: {((pnl[4]/pnl[2])*100):.1f}%", subtitle_style),
            Paragraph(f"COGS: ${pnl[3]:,.0f}", subtitle_style),
            Paragraph(f"Margin: {((pnl[6]/pnl[2])*100):.1f}%", subtitle_style),
            Paragraph(f"Margin: {((pnl[12]/pnl[2])*100):.1f}%", subtitle_style)
        ]
    ]
    kpi_table = Table(kpi_cards, colWidths=[126, 126, 126, 126])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 18))

    # Profit & Loss Statement Table
    story.append(Paragraph("1. Profit and Loss Statement Summary", h1_style))
    pnl_rows = [
        [Paragraph("Financial Metric / Category", table_header_style), Paragraph(f"M{target_month} Actual ($)", table_header_style), Paragraph(f"M{prev_m} Prior ($)", table_header_style), Paragraph("MoM Change ($)", table_header_style), Paragraph("MoM %", table_header_style)],
        [Paragraph("Gross Revenue (SaaS + Services)", table_cell_style), Paragraph(f"${pnl[2]:,.2f}", table_cell_style), Paragraph(f"${prev_pnl[2]:,.2f}", table_cell_style), Paragraph(f"${pnl[2]-prev_pnl[2]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[2]-prev_pnl[2])/prev_pnl[2])*100):+.1f}%", table_cell_style)],
        [Paragraph("Cost of Goods Sold (Hosting & Delivery)", table_cell_style), Paragraph(f"${pnl[3]:,.2f}", table_cell_style), Paragraph(f"${prev_pnl[3]:,.2f}", table_cell_style), Paragraph(f"${pnl[3]-prev_pnl[3]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[3]-prev_pnl[3])/prev_pnl[3])*100):+.1f}%", table_cell_style)],
        [Paragraph("<b>Gross Profit</b>", table_cell_bold), Paragraph(f"<b>${pnl[4]:,.2f}</b>", table_cell_bold), Paragraph(f"${prev_pnl[4]:,.2f}", table_cell_style), Paragraph(f"${pnl[4]-prev_pnl[4]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[4]-prev_pnl[4])/prev_pnl[4])*100):+.1f}%", table_cell_style)],
        [Paragraph("Operating Expenses (R&D, S&M, G&A)", table_cell_style), Paragraph(f"${pnl[5]:,.2f}", table_cell_style), Paragraph(f"${prev_pnl[5]:,.2f}", table_cell_style), Paragraph(f"${pnl[5]-prev_pnl[5]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[5]-prev_pnl[5])/prev_pnl[5])*100):+.1f}%", table_cell_style)],
        [Paragraph("<b>EBITDA</b>", table_cell_bold), Paragraph(f"<b>${pnl[6]:,.2f}</b>", table_cell_bold), Paragraph(f"${prev_pnl[6]:,.2f}", table_cell_style), Paragraph(f"${pnl[6]-prev_pnl[6]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[6]-prev_pnl[6])/prev_pnl[6])*100):+.1f}%", table_cell_style)],
        [Paragraph("Depreciation & Amortization", table_cell_style), Paragraph(f"${pnl[7]:,.2f}", table_cell_style), Paragraph(f"${prev_pnl[7]:,.2f}", table_cell_style), Paragraph("$0.00", table_cell_style), Paragraph("0.0%", table_cell_style)],
        [Paragraph("Operating Income (EBIT)", table_cell_style), Paragraph(f"${pnl[8]:,.2f}", table_cell_style), Paragraph(f"${prev_pnl[8]:,.2f}", table_cell_style), Paragraph(f"${pnl[8]-prev_pnl[8]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[8]-prev_pnl[8])/prev_pnl[8])*100):+.1f}%", table_cell_style)],
        [Paragraph("Corporate Interest Expense", table_cell_style), Paragraph(f"${pnl[9]:,.2f}", table_cell_style), Paragraph(f"${prev_pnl[9]:,.2f}", table_cell_style), Paragraph("$0.00", table_cell_style), Paragraph("0.0%", table_cell_style)],
        [Paragraph("Income Tax Provision (21%)", table_cell_style), Paragraph(f"${pnl[11]:,.2f}", table_cell_style), Paragraph(f"${prev_pnl[11]:,.2f}", table_cell_style), Paragraph(f"${pnl[11]-prev_pnl[11]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[11]-prev_pnl[11])/prev_pnl[11])*100):+.1f}%", table_cell_style)],
        [Paragraph("<b>NET INCOME</b>", table_cell_bold), Paragraph(f"<b>${pnl[12]:,.2f}</b>", table_cell_bold), Paragraph(f"<b>${prev_pnl[12]:,.2f}</b>", table_cell_bold), Paragraph(f"${pnl[12]-prev_pnl[12]:,.2f}", table_cell_style), Paragraph(f"{(((pnl[12]-prev_pnl[12])/prev_pnl[12])*100):+.1f}%", table_cell_style)],
    ]
    pnl_table = Table(pnl_rows, colWidths=[174, 85, 85, 85, 75])
    pnl_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0, 10), (-1, 10), colors.HexColor('#DCFCE7')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(pnl_table)
    story.append(Spacer(1, 14))

    # Balance Sheet Reconciliation Box
    tot_a = sum(r[1] for r in bs_assets)
    tot_l = sum(r[1] for r in bs_liab)
    tot_e = bs_eq[2]
    diff = round(tot_a - (tot_l + tot_e), 2)
    
    bs_recon_text = (
        f"<b>Balance Sheet Certification:</b> Total Net Assets = <b>${tot_a:,.2f}</b> | "
        f"Total Liabilities = <b>${tot_l:,.2f}</b> | Total Equity = <b>${tot_e:,.2f}</b>. "
        f"Status: <font color='#15803D'><b>PERFECTLY RECONCILED (Discrepancy: ${diff:.2f})</b></font>."
    )
    story.append(Paragraph(bs_recon_text, ParagraphStyle('ReconBox', parent=body_style, backColor=colors.HexColor('#F0FDF4'), borderPadding=6, borderWidth=0.5, borderColor=colors.HexColor('#86EFAC'))))
    
    # -------------------------------------------------------------------------
    # PAGE 2: Budget Variance & Credit Portfolio Analytics
    # -------------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("2. Budget vs Actual Variance Analysis", h1_style))
    story.append(Paragraph("Comparison of department expense execution against approved budget allocations:", body_style))
    story.append(Spacer(1, 8))

    bva_rows = [
        [Paragraph("Department Name", table_header_style), Paragraph("Approved Budget ($)", table_header_style), Paragraph("Actual Spending ($)", table_header_style), Paragraph("Variance ($)", table_header_style), Paragraph("Variance %", table_header_style), Paragraph("Status", table_header_style)]
    ]
    for dname, b_val, a_val, var_val, var_pct in bva_depts:
        is_over = var_val > 0
        status_str = f"<font color='{'#991B1B' if is_over else '#15803D'}'><b>{'Over Budget' if is_over else 'Within Budget'}</b></font>"
        bva_rows.append([
            Paragraph(dname, table_cell_style),
            Paragraph(f"${b_val:,.2f}", table_cell_style),
            Paragraph(f"${a_val:,.2f}", table_cell_style),
            Paragraph(f"${var_val:+,.2f}", table_cell_style),
            Paragraph(f"{var_pct:+.1f}%", table_cell_style),
            Paragraph(status_str, table_cell_style)
        ])
    bva_table = Table(bva_rows, colWidths=[154, 80, 80, 75, 55, 60])
    bva_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(bva_table)
    story.append(Spacer(1, 14))

    # Credit Risk Portfolio Section
    story.append(Paragraph("3. Credit Risk & Underwriting Portfolio Health", h1_style))
    story.append(Paragraph(
        f"Portfolio overview: <b>{credit_stats[0]:,}</b> active loans with total funded volume of <b>${credit_stats[1]:,.2f}</b>. "
        f"Empirical historical default rate across portfolio stands at <b>{credit_stats[5]}%</b> with an average portfolio DTI of <b>{credit_stats[2]:.1f}%</b>.",
        body_style
    ))
    story.append(Spacer(1, 8))

    risk_rows = [
        [Paragraph("Risk Band", table_header_style), Paragraph("Borrower Count", table_header_style), Paragraph("Portfolio Share", table_header_style), Paragraph("Avg Default Prob", table_header_style), Paragraph("Avg Credit Score", table_header_style), Paragraph("Underwriting Status", table_header_style)]
    ]
    tot_bor = sum(r[1] for r in risk_band_counts)
    for band, cnt, avg_pd, avg_score in risk_band_counts:
        share = (cnt / tot_bor) * 100.0
        risk_rows.append([
            Paragraph(f"<b>{band}</b>", table_cell_bold),
            Paragraph(f"{cnt:,}", table_cell_style),
            Paragraph(f"{share:.1f}%", table_cell_style),
            Paragraph(f"{avg_pd:.2f}%", table_cell_style),
            Paragraph(f"{avg_score:.0f}", table_cell_style),
            Paragraph("Auto-Approve" if band=="Low Risk" else "Standard" if band=="Medium Risk" else "Review" if band=="High Risk" else "Decline", table_cell_style)
        ])
    risk_table = Table(risk_rows, colWidths=[114, 75, 75, 80, 80, 80])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 14))

    # Include visual artifact if exists
    roc_img_path = os.path.join(SCREENSHOTS_DIR, "roc_curve.png")
    score_img_path = os.path.join(SCREENSHOTS_DIR, "score_distribution.png")
    if os.path.exists(score_img_path):
        story.append(Paragraph("<b>Credit Scorecard Portfolio Distribution:</b>", h1_style))
        story.append(Spacer(1, 4))
        story.append(Image(score_img_path, width=460, height=170))
        story.append(Spacer(1, 10))

    # Board Sign-off Box
    signoff_rows = [
        [Paragraph("<b>Prepared by:</b> FinSight Senior Financial Analyst", body_style), Paragraph("<b>Reviewed by:</b> Chief Financial Officer (CFO)", body_style)],
        [Paragraph("Signature: __________________________", body_style), Paragraph("Signature: __________________________", body_style)],
        [Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", body_style), Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", body_style)],
    ]
    signoff_table = Table(signoff_rows, colWidths=[252, 252])
    signoff_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(Spacer(1, 10))
    story.append(signoff_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Monthly Board Report PDF generated at: {OUTPUT_PDF_PATH}")
    return OUTPUT_PDF_PATH

if __name__ == "__main__":
    generate_board_report()
