import pandas as pd
import io
import xlsxwriter

def write_formatted_sheet(workbook, worksheet, final_df, detected_date_str, years_text):
    title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
    subtitle_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFE699', 'border': 1})
    date_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'italic': True, 'border': 1})
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFD966', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    center_fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
    total_fmt = workbook.add_format({'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'align': 'center', 'valign': 'vcenter'}) 
    grand_total_fmt = workbook.add_format({'bold': True, 'bg_color': '#F4B084', 'border': 1, 'align': 'center', 'valign': 'vcenter'}) 

    worksheet.merge_range('A1:I1', "OFFICE OF THE CONTROLLER OF EXAMINATIONS", title_fmt)
    worksheet.merge_range('A2:I2', f"Date: {detected_date_str}", date_fmt) 
    worksheet.merge_range('A3:I3', f"{years_text} YEAR SKILL RACK RESULT ANALYSIS", subtitle_fmt)
    
    worksheet.merge_range('A4:A5', "Branch", header_fmt)
    worksheet.merge_range('B4:B5', "Year", header_fmt)
    worksheet.merge_range('C4:E4', "Student Strength Details", header_fmt)
    worksheet.merge_range('F4:I4', "No of Problems Solved", header_fmt)
    
    col_names = ["Registered", "Appeared", "Absent", "Zero", "One", "Two", "Three"]
    for i, name in enumerate(col_names):
        worksheet.write(4, 2 + i, name, header_fmt)

    start_row = 5
    col_keys = ["Branch", "Year", "No of Registered Students", "No of Students Appeared", "No of Students Absent", "Zero Problems Solved", "One Problem Solved", "Two Problems Solved", "Three Problems Solved"]
    records = final_df.to_dict('records')

    current_branch = None
    branch_start_idx = -1

    for i, row_data in enumerate(records):
        row_idx = start_row + i
        branch_val = row_data['Branch']
        
        if "OVERALL TOTAL" in str(branch_val):
            if current_branch and branch_start_idx != -1:
                if (row_idx - 1) > branch_start_idx:
                    worksheet.merge_range(branch_start_idx, 0, row_idx - 1, 0, current_branch, center_fmt)
                else:
                    worksheet.write(branch_start_idx, 0, current_branch, center_fmt)
            fmt = grand_total_fmt
            worksheet.merge_range(row_idx, 0, row_idx, 1, "OVERALL TOTAL", fmt)
            for col_num in range(2, 9):
                worksheet.write(row_idx, col_num, row_data[col_keys[col_num]], fmt)
        elif "TOTAL" in str(branch_val):
            fmt = total_fmt
            worksheet.merge_range(row_idx, 0, row_idx, 1, "TOTAL", fmt)
            for col_num in range(2, 9):
                worksheet.write(row_idx, col_num, row_data[col_keys[col_num]], fmt)
            if current_branch and branch_start_idx != -1:
                if (row_idx - 1) > branch_start_idx:
                    worksheet.merge_range(branch_start_idx, 0, row_idx - 1, 0, current_branch, center_fmt)
                else:
                    worksheet.write(branch_start_idx, 0, current_branch, center_fmt)
            current_branch = None
            branch_start_idx = -1
        else:
            fmt = center_fmt
            for col_num in range(9):
                worksheet.write(row_idx, col_num, str(row_data[col_keys[col_num]]), fmt)
            if branch_val != current_branch:
                if current_branch is not None:
                    if (row_idx - 1) > branch_start_idx:
                        worksheet.merge_range(branch_start_idx, 0, row_idx - 1, 0, current_branch, center_fmt)
                    else:
                        worksheet.write(branch_start_idx, 0, current_branch, center_fmt)
                current_branch = branch_val
                branch_start_idx = row_idx

    worksheet.set_column('A:A', 20) 
    worksheet.set_column('B:B', 15) 
    worksheet.set_column('C:I', 15)

def generate_excel_report(reports_data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        for rep in reports_data:
            df = pd.DataFrame(rep['data'])
            sheet_name = f"{rep['date']}"[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=5, header=False)
            write_formatted_sheet(workbook, writer.sheets[sheet_name], df, rep['date'], rep['years_text'])
    return output.getvalue()

def generate_weekly_excel(weekly_data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df = pd.DataFrame(weekly_data)
        df.to_excel(writer, index=False, sheet_name='Weekly Leaderboard')
        
        workbook = writer.book
        worksheet = writer.sheets['Weekly Leaderboard']
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFD966', 'border': 1})
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15)
            
    return output.getvalue()

def generate_performance_excel(performance_data, branch, top_n):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df = pd.DataFrame(performance_data)
        # Ensure Reg No is prominently placed if it exists
        cols = df.columns.tolist()
        if 'Reg No' in cols:
            cols.insert(0, cols.pop(cols.index('Reg No')))
            df = df[cols]
            
        sheet_name = f'Top {top_n} {branch}'[:31]
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFD966', 'border': 1})
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15)
            
    return output.getvalue()
