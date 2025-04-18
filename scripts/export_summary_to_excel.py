
# export_summary_to_excel.py

import pandas as pd
import xlsxwriter

def export_summary_to_excel(df, filename="output.xlsx"):
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Summary')

    workbook  = writer.book
    worksheet = writer.sheets['Summary']
    format1 = workbook.add_format({'num_format': '#,##0', 'bold': True})
    worksheet.set_column('A:Z', 18, format1)

    writer.close()
