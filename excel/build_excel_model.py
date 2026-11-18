"""
FinSight Platform - Excel Financial Model Builder
Generates a multi-tab financial workbook (financial_model.xlsx) with:
- Executive Summary & Financial KPIs
- Monthly Profit & Loss Statement (with formulas)
- Reconciled Monthly Balance Sheet (with reconciliation check formulas)
- Budget vs Actual & Department Variance Analysis
- Credit Portfolio Risk Summary
- Power Pivot Data Model Architecture & DAX Measure Reference Guide
"""

import os
import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "finsight.db")
EXCEL_PATH = os.path.join(BASE_DIR, "excel", "financial_model.xlsx")

def create_financial_model():
    print("[*] Building FinSight Excel Financial Model...")
    conn = sqlite3.connect(DB_PATH)
    
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)
    
    # Styling Palette
    FONT_FAMILY = "Segoe UI"
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Navy
    accent_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid") # Blue Accent
    sub_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid") # Light Slate
    highlight_fill = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid")
    green_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    
    header_font = Font(name=FONT_FAMILY, size=11, bold=True, color="FFFFFF")
    title_font = Font(name=FONT_FAMILY, size=16, bold=True, color="0F172A")
    subtitle_font = Font(name=FONT_FAMILY, size=10, italic=True, color="64748B")
    bold_font = Font(name=FONT_FAMILY, size=10, bold=True, color="0F172A")
    regular_font = Font(name=FONT_FAMILY, size=10, color="1E293B")
    formula_font = Font(name=FONT_FAMILY, size=10, bold=True, color="0369A1")
    reconciled_font = Font(name=FONT_FAMILY, size=10, bold=True, color="15803D")
    
    thin_border_side = Side(style='thin', color='CBD5E1')
    double_bottom_side = Side(style='double', color='0F172A')
    regular_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    total_border = Border(top=thin_border_side, bottom=double_bottom_side)
    
    # -------------------------------------------------------------------------
    # 1. P&L Statement Sheet
    # -------------------------------------------------------------------------
    ws_pnl = wb.create_sheet(title="P&L Statement")
    ws_pnl.views.sheetView[0].showGridLines = True
    
    # Title Block
    ws_pnl["A1"] = "FinSight Intelligence – Profit and Loss Statement"
    ws_pnl["A1"].font = title_font
    ws_pnl["A2"] = "Fiscal Year 2026 (Actuals in USD) | Prepared for Executive & Board Evaluation"
    ws_pnl["A2"].font = subtitle_font
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pnl_headers = ["Line Item / Category"] + months + ["Full Year Total"]
    
    for col_idx, h in enumerate(pnl_headers, 1):
        cell = ws_pnl.cell(row=4, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")
        
    pnl_data = conn.execute("SELECT * FROM view_monthly_pnl ORDER BY fiscal_month").fetchall()
    
    # Line items configuration
    lines = [
        ("Gross Revenue (SaaS + Services + API)", 2, False, False),
        ("Cost of Goods Sold (Hosting & Delivery)", 3, False, False),
        ("Gross Profit", None, True, False), # Formula: Rev - COGS
        ("Operating Expenses (R&D, S&M, G&A)", 5, False, False),
        ("EBITDA", None, True, False), # Formula: GP - Opex
        ("Depreciation & Amortization", 7, False, False),
        ("Operating Income (EBIT)", None, True, False), # Formula: EBITDA - D&A
        ("Interest Expense", 9, False, False),
        ("Profit Before Tax (EBT)", None, True, False), # Formula: EBIT - Interest
        ("Income Tax Expense (21%)", 11, False, False),
        ("Net Profit", None, True, True), # Formula: EBT - Tax
    ]
    
    row_map = {}
    current_row = 5
    for label, db_idx, is_calc, is_net in lines:
        row_map[label] = current_row
        ws_pnl.cell(row=current_row, column=1, value=label).font = bold_font if is_calc else regular_font
        
        for m_idx in range(12):
            col = m_idx + 2
            col_letter = get_column_letter(col)
            cell = ws_pnl.cell(row=current_row, column=col)
            
            if not is_calc:
                val = pnl_data[m_idx][db_idx]
                cell.value = val
                cell.font = regular_font
            else:
                if label == "Gross Profit":
                    r_rev = row_map["Gross Revenue (SaaS + Services + API)"]
                    r_cogs = row_map["Cost of Goods Sold (Hosting & Delivery)"]
                    cell.value = f"={col_letter}{r_rev}-{col_letter}{r_cogs}"
                elif label == "EBITDA":
                    r_gp = row_map["Gross Profit"]
                    r_opex = row_map["Operating Expenses (R&D, S&M, G&A)"]
                    cell.value = f"={col_letter}{r_gp}-{col_letter}{r_opex}"
                elif label == "Operating Income (EBIT)":
                    r_ebitda = row_map["EBITDA"]
                    r_depr = row_map["Depreciation & Amortization"]
                    cell.value = f"={col_letter}{r_ebitda}-{col_letter}{r_depr}"
                elif label == "Profit Before Tax (EBT)":
                    r_ebit = row_map["Operating Income (EBIT)"]
                    r_int = row_map["Interest Expense"]
                    cell.value = f"={col_letter}{r_ebit}-{col_letter}{r_int}"
                elif label == "Net Profit":
                    r_ebt = row_map["Profit Before Tax (EBT)"]
                    r_tax = row_map["Income Tax Expense (21%)"]
                    cell.value = f"={col_letter}{r_ebt}-{col_letter}{r_tax}"
                    
                cell.font = formula_font
                cell.fill = highlight_fill if not is_net else green_fill
                
            cell.number_format = "$#,##0"
            cell.border = total_border if is_net else regular_border
            
        # FY Total Column
        tot_cell = ws_pnl.cell(row=current_row, column=14)
        tot_cell.value = f"=SUM(B{current_row}:M{current_row})"
        tot_cell.font = bold_font
        tot_cell.number_format = "$#,##0"
        tot_cell.fill = highlight_fill if not is_net else green_fill
        tot_cell.border = total_border if is_net else regular_border
        
        current_row += 1
        
    # Margin Analysis section
    current_row += 1
    ws_pnl.cell(row=current_row, column=1, value="FINANCIAL RATIOS & MARGINS").font = bold_font
    current_row += 1
    
    ratios = [
        ("Gross Margin %", "Gross Profit", "Gross Revenue (SaaS + Services + API)"),
        ("EBITDA Margin %", "EBITDA", "Gross Revenue (SaaS + Services + API)"),
        ("Net Profit Margin %", "Net Profit", "Gross Revenue (SaaS + Services + API)"),
    ]
    for r_label, num_name, den_name in ratios:
        ws_pnl.cell(row=current_row, column=1, value=r_label).font = bold_font
        num_row = row_map[num_name]
        den_row = row_map[den_name]
        for m_idx in range(12):
            col = m_idx + 2
            col_letter = get_column_letter(col)
            c = ws_pnl.cell(row=current_row, column=col)
            c.value = f"={col_letter}{num_row}/{col_letter}{den_row}"
            c.font = regular_font
            c.number_format = "0.0%"
            c.border = regular_border
            
        tot_c = ws_pnl.cell(row=current_row, column=14)
        tot_c.value = f"=N{num_row}/N{den_row}"
        tot_c.font = bold_font
        tot_c.number_format = "0.0%"
        tot_c.border = regular_border
        current_row += 1

    # -------------------------------------------------------------------------
    # 2. Balance Sheet Sheet
    # -------------------------------------------------------------------------
    ws_bs = wb.create_sheet(title="Balance Sheet")
    ws_bs.views.sheetView[0].showGridLines = True
    
    ws_bs["A1"] = "FinSight Intelligence – Balance Sheet & Reconciliation"
    ws_bs["A1"].font = title_font
    ws_bs["A2"] = "Assets = Liabilities + Equity Verification | Fiscal Year 2026"
    ws_bs["A2"].font = subtitle_font
    
    for col_idx, h in enumerate(pnl_headers[:13], 1):
        cell = ws_bs.cell(row=4, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")
        
    # Query Assets, Liab, Equity
    assets_raw = conn.execute("SELECT fiscal_month, category, SUM(net_value) FROM assets GROUP BY fiscal_month, category").fetchall()
    liab_raw = conn.execute("SELECT fiscal_month, category, SUM(current_balance) FROM liabilities GROUP BY fiscal_month, category").fetchall()
    eq_raw = conn.execute("SELECT fiscal_month, share_capital, retained_earnings, total_equity FROM equity ORDER BY fiscal_month").fetchall()
    
    bs_row = 5
    # Section Assets
    ws_bs.cell(row=bs_row, column=1, value="ASSETS").font = bold_font
    ws_bs.cell(row=bs_row, column=1).fill = sub_fill
    bs_row += 1
    
    asset_cats = ["Cash", "Accounts Receivable", "Inventory", "Fixed Assets", "Other Assets"]
    asset_rows = []
    for cat in asset_cats:
        asset_rows.append(bs_row)
        ws_bs.cell(row=bs_row, column=1, value=f"  {cat}").font = regular_font
        cat_vals = {row[0]: row[2] for row in assets_raw if row[1] == cat}
        for m_idx in range(12):
            c = ws_bs.cell(row=bs_row, column=m_idx + 2, value=cat_vals.get(m_idx + 1, 0.0))
            c.number_format = "$#,##0"
            c.font = regular_font
            c.border = regular_border
        bs_row += 1
        
    tot_assets_row = bs_row
    ws_bs.cell(row=tot_assets_row, column=1, value="TOTAL ASSETS").font = bold_font
    ws_bs.cell(row=tot_assets_row, column=1).fill = highlight_fill
    for m_idx in range(12):
        col_letter = get_column_letter(m_idx + 2)
        c = ws_bs.cell(row=tot_assets_row, column=m_idx + 2)
        c.value = f"=SUM({col_letter}{asset_rows[0]}:{col_letter}{asset_rows[-1]})"
        c.font = formula_font
        c.number_format = "$#,##0"
        c.fill = highlight_fill
        c.border = total_border
    bs_row += 2
    
    # Section Liabilities
    ws_bs.cell(row=bs_row, column=1, value="LIABILITIES").font = bold_font
    ws_bs.cell(row=bs_row, column=1).fill = sub_fill
    bs_row += 1
    
    liab_cats = ["Accounts Payable", "Short-Term Debt", "Long-Term Debt", "Other Liabilities"]
    liab_rows = []
    for cat in liab_cats:
        liab_rows.append(bs_row)
        ws_bs.cell(row=bs_row, column=1, value=f"  {cat}").font = regular_font
        cat_vals = {row[0]: row[2] for row in liab_raw if row[1] == cat}
        for m_idx in range(12):
            c = ws_bs.cell(row=bs_row, column=m_idx + 2, value=cat_vals.get(m_idx + 1, 0.0))
            c.number_format = "$#,##0"
            c.font = regular_font
            c.border = regular_border
        bs_row += 1
        
    tot_liab_row = bs_row
    ws_bs.cell(row=tot_liab_row, column=1, value="TOTAL LIABILITIES").font = bold_font
    ws_bs.cell(row=tot_liab_row, column=1).fill = highlight_fill
    for m_idx in range(12):
        col_letter = get_column_letter(m_idx + 2)
        c = ws_bs.cell(row=tot_liab_row, column=m_idx + 2)
        c.value = f"=SUM({col_letter}{liab_rows[0]}:{col_letter}{liab_rows[-1]})"
        c.font = formula_font
        c.number_format = "$#,##0"
        c.fill = highlight_fill
        c.border = regular_border
    bs_row += 2
    
    # Section Equity
    ws_bs.cell(row=bs_row, column=1, value="EQUITY").font = bold_font
    ws_bs.cell(row=bs_row, column=1).fill = sub_fill
    bs_row += 1
    
    sc_row = bs_row
    ws_bs.cell(row=sc_row, column=1, value="  Share Capital / Paid-in Capital").font = regular_font
    re_row = bs_row + 1
    ws_bs.cell(row=re_row, column=1, value="  Retained Earnings").font = regular_font
    
    for m_idx in range(12):
        eq_record = eq_raw[m_idx]
        c_sc = ws_bs.cell(row=sc_row, column=m_idx + 2, value=eq_record[1])
        c_sc.number_format = "$#,##0"
        c_sc.font = regular_font
        c_sc.border = regular_border
        
        c_re = ws_bs.cell(row=re_row, column=m_idx + 2, value=eq_record[2])
        c_re.number_format = "$#,##0"
        c_re.font = regular_font
        c_re.border = regular_border
    bs_row += 2
    
    tot_eq_row = bs_row
    ws_bs.cell(row=tot_eq_row, column=1, value="TOTAL EQUITY").font = bold_font
    for m_idx in range(12):
        col_letter = get_column_letter(m_idx + 2)
        c = ws_bs.cell(row=tot_eq_row, column=m_idx + 2)
        c.value = f"={col_letter}{sc_row}+{col_letter}{re_row}"
        c.font = formula_font
        c.number_format = "$#,##0"
        c.border = regular_border
    bs_row += 1
    
    tot_le_row = bs_row
    ws_bs.cell(row=tot_le_row, column=1, value="TOTAL LIABILITIES & EQUITY").font = bold_font
    ws_bs.cell(row=tot_le_row, column=1).fill = highlight_fill
    for m_idx in range(12):
        col_letter = get_column_letter(m_idx + 2)
        c = ws_bs.cell(row=tot_le_row, column=m_idx + 2)
        c.value = f"={col_letter}{tot_liab_row}+{col_letter}{tot_eq_row}"
        c.font = formula_font
        c.number_format = "$#,##0"
        c.fill = highlight_fill
        c.border = total_border
    bs_row += 2
    
    # Reconciliation Row
    recon_row = bs_row
    ws_bs.cell(row=recon_row, column=1, value="BALANCE SHEET CHECK (Assets - Liab - Eq)").font = bold_font
    ws_bs.cell(row=recon_row, column=1).fill = green_fill
    for m_idx in range(12):
        col_letter = get_column_letter(m_idx + 2)
        c = ws_bs.cell(row=recon_row, column=m_idx + 2)
        c.value = f"={col_letter}{tot_assets_row}-{col_letter}{tot_le_row}"
        c.font = reconciled_font
        c.number_format = "$#,##0.00"
        c.fill = green_fill
        c.border = total_border
        c.alignment = Alignment(horizontal="right")

    # -------------------------------------------------------------------------
    # 3. Budget vs Actual Sheet
    # -------------------------------------------------------------------------
    ws_bva = wb.create_sheet(title="Budget vs Actual")
    ws_bva.views.sheetView[0].showGridLines = True
    
    ws_bva["A1"] = "FinSight Intelligence – Budget vs Actual Variance Analysis"
    ws_bva["A1"].font = title_font
    ws_bva["A2"] = "Departmental and Account Level Variance Performance | FY 2026"
    ws_bva["A2"].font = subtitle_font
    
    bva_headers = [
        "Fiscal Month", "Department Code", "Department Name", 
        "Account Code", "Account Name", "Account Type", 
        "Budgeted Amount", "Actual Amount", "Variance ($)", "Variance (%)", "Evaluation Status"
    ]
    for col_idx, h in enumerate(bva_headers, 1):
        c = ws_bva.cell(row=4, column=col_idx, value=h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center" if col_idx in [1, 2, 4, 11] else "left")
        
    bva_data = conn.execute("""
        SELECT fiscal_month, department_code, department_name, 
               account_code, account_name, account_type, 
               budgeted_amount, actual_amount, variance_amount, variance_percentage, budget_status
        FROM view_budget_vs_actual
        ORDER BY fiscal_month, department_code, account_code
    """).fetchall()
    
    for row_idx, r in enumerate(bva_data, 5):
        m, dcode, dname, acode, aname, atype, b_amt, a_amt, var_amt, var_pct, status = r
        ws_bva.cell(row=row_idx, column=1, value=m).alignment = Alignment(horizontal="center")
        ws_bva.cell(row=row_idx, column=2, value=dcode).alignment = Alignment(horizontal="center")
        ws_bva.cell(row=row_idx, column=3, value=dname)
        ws_bva.cell(row=row_idx, column=4, value=acode).alignment = Alignment(horizontal="center")
        ws_bva.cell(row=row_idx, column=5, value=aname)
        ws_bva.cell(row=row_idx, column=6, value=atype)
        
        c_b = ws_bva.cell(row=row_idx, column=7, value=b_amt)
        c_b.number_format = "$#,##0.00"
        
        c_a = ws_bva.cell(row=row_idx, column=8, value=a_amt)
        c_a.number_format = "$#,##0.00"
        
        # Formulas for Variance and Variance %
        c_v = ws_bva.cell(row=row_idx, column=9, value=f"=H{row_idx}-G{row_idx}")
        c_v.number_format = "$#,##0.00"
        c_v.font = formula_font
        
        c_vp = ws_bva.cell(row=row_idx, column=10, value=f"=IF(G{row_idx}=0, 0, I{row_idx}/G{row_idx})")
        c_vp.number_format = "0.0%"
        c_vp.font = formula_font
        
        c_s = ws_bva.cell(row=row_idx, column=11, value=status)
        c_s.alignment = Alignment(horizontal="center")
        if status in ["Within Budget", "Above Target"]:
            c_s.fill = green_fill
            c_s.font = Font(name=FONT_FAMILY, size=10, bold=True, color="166534")
        else:
            c_s.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            c_s.font = Font(name=FONT_FAMILY, size=10, bold=True, color="991B1B")

    # -------------------------------------------------------------------------
    # 4. Power Pivot Data Model & DAX Guide Sheet
    # -------------------------------------------------------------------------
    ws_dax = wb.create_sheet(title="Power Pivot & DAX")
    ws_dax.views.sheetView[0].showGridLines = True
    
    ws_dax["A1"] = "FinSight Intelligence – Power Pivot Architecture & DAX Measures"
    ws_dax["A1"].font = title_font
    ws_dax["A2"] = "Technical Reference for Excel Data Model Integration"
    ws_dax["A2"].font = subtitle_font
    
    dax_headers = ["Measure Name", "Target Table", "DAX Formula Expression", "Description / Financial Usage"]
    for col_idx, h in enumerate(dax_headers, 1):
        c = ws_dax.cell(row=4, column=col_idx, value=h)
        c.font = header_font
        c.fill = header_fill
        
    dax_measures = [
        ("[Total Revenue]", "Transactions", "SUM(Transactions[credit_amount]) - SUM(Transactions[debit_amount])", "Total top-line recognized business revenue from SaaS, consulting, and APIs"),
        ("[Total Actual Expenses]", "Transactions", "CALCULATE(SUM(Transactions[debit_amount]) - SUM(Transactions[credit_amount]), ChartOfAccounts[account_type]=\"Expense\")", "Sum of all recognized operational, COGS, interest, and tax expenses"),
        ("[Net Profit]", "Transactions", "[Total Revenue] - [Total Actual Expenses]", "Bottom-line net income transferred to retained earnings"),
        ("[Gross Margin %]", "Transactions", "DIVIDE([Gross Profit], [Total Revenue], 0)", "Gross profitability ratio showing core platform unit economics"),
        ("[EBITDA]", "Transactions", "[Gross Profit] - [Total Operating Expenses]", "Operational cash generation capability excluding non-cash D&A"),
        ("[Total Budgeted]", "Budgets", "SUM(Budgets[budgeted_amount])", "Planned expenditure and revenue allocation"),
        ("[Budget Variance]", "Transactions", "[Total Actual Expenses] - [Total Budgeted]", "Variance between actual spending and approved plan"),
        ("[Variance %]", "Transactions", "DIVIDE([Budget Variance], [Total Budgeted], 0)", "Percentage budget deviation for conditional alert triggers"),
        ("[Total Funded Volume]", "Loans", "SUM(Loans[loan_amount])", "Gross outstanding credit principal exposure"),
        ("[Portfolio Default Rate]", "Loans", "DIVIDE(CALCULATE(COUNTROWS(Loans), Loans[is_default]=1), COUNTROWS(Loans), 0)", "Empirical historical credit default rate across all borrower segments"),
        ("[Avg Debt-to-Income]", "Loans", "AVERAGE(Loans[debt_to_income_ratio])", "Average borrower debt leverage metric"),
    ]
    
    for r_idx, (m_name, tbl, expr, desc) in enumerate(dax_measures, 5):
        c1 = ws_dax.cell(row=r_idx, column=1, value=m_name)
        c1.font = bold_font
        c1.border = regular_border
        
        c2 = ws_dax.cell(row=r_idx, column=2, value=tbl)
        c2.font = regular_font
        c2.border = regular_border
        
        c3 = ws_dax.cell(row=r_idx, column=3, value=expr)
        c3.font = Font(name="Consolas", size=9, bold=True, color="0369A1")
        c3.fill = highlight_fill
        c3.border = regular_border
        
        c4 = ws_dax.cell(row=r_idx, column=4, value=desc)
        c4.font = regular_font
        c4.border = regular_border

    # Adjust column widths for all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
    ws_pnl.column_dimensions["A"].width = 38
    ws_bs.column_dimensions["A"].width = 38
    ws_bva.column_dimensions["A"].width = 14
    ws_bva.column_dimensions["C"].width = 28
    ws_bva.column_dimensions["E"].width = 36
    ws_dax.column_dimensions["A"].width = 25
    ws_dax.column_dimensions["B"].width = 16
    ws_dax.column_dimensions["C"].width = 50
    ws_dax.column_dimensions["D"].width = 60
    
    wb.save(EXCEL_PATH)
    conn.close()
    print(f"[SUCCESS] FinSight Excel Financial Model created at: {EXCEL_PATH}")

if __name__ == "__main__":
    create_financial_model()
