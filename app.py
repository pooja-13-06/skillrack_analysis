import streamlit as st
import pandas as pd
import io
import database # Import the new db module
import hmac
from datetime import datetime
import re

database.init_db()

def write_formatted_sheet(workbook, worksheet, final_df, detected_date_str, years_text):
    """
    Helper function to write a professional analysis report to a specific worksheet.
    Used for multi-sheet Excel generation.
    """
    # formats
    title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
    subtitle_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFE699', 'border': 1})
    date_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'italic': True, 'border': 1})
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFD966', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    center_fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
    total_fmt = workbook.add_format({'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'align': 'center', 'valign': 'vcenter'}) 
    grand_total_fmt = workbook.add_format({'bold': True, 'bg_color': '#F4B084', 'border': 1, 'align': 'center', 'valign': 'vcenter'}) 

    # Data: Starts R6 (Header in R4/R5)
    # final_df.to_excel(writer...) is called outside, but we manage the content here
    
    subtitle_text = f"{years_text} YEAR SKILL RACK RESULT ANALYSIS"
    date_text = f"Date: {detected_date_str}"

    # Headers
    worksheet.merge_range('A1:I1', "OFFICE OF THE CONTROLLER OF EXAMINATIONS", title_fmt)
    worksheet.merge_range('A2:I2', date_text, date_fmt) 
    worksheet.merge_range('A3:I3', subtitle_text, subtitle_fmt)
    
    worksheet.merge_range('A4:A5', "Branch", header_fmt)
    worksheet.merge_range('B4:B5', "Year", header_fmt)
    worksheet.merge_range('C4:E4', "Student Strength Details", header_fmt)
    worksheet.merge_range('F4:I4', "No of Problems Solved", header_fmt)
    
    worksheet.write('C5', "Registered", header_fmt)
    worksheet.write('D5', "Appeared", header_fmt)
    worksheet.write('E5', "Absent", header_fmt)
    worksheet.write('F5', "Zero", header_fmt)
    worksheet.write('G5', "One", header_fmt)
    worksheet.write('H5', "Two", header_fmt)
    worksheet.write('I5', "Three", header_fmt)

    # Apply Row Styles
    start_row = 5
    records = final_df.to_dict('records')
    col_keys = ["Branch", "Year", "No of Registered Students", "No of Students Appeared", "No of Students Absent", "Zero Problems Solved", "One Problem Solved", "Two Problems Solved", "Three Problems Solved"]

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
                key = col_keys[col_num]
                worksheet.write(row_idx, col_num, row_data[key], fmt)
                
        elif "TOTAL" in str(branch_val):
            fmt = total_fmt
            worksheet.merge_range(row_idx, 0, row_idx, 1, "TOTAL", fmt)
            for col_num in range(2, 9):
                key = col_keys[col_num]
                worksheet.write(row_idx, col_num, row_data[key], fmt)
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
                key = col_keys[col_num]
                worksheet.write(row_idx, col_num, row_data[key], fmt)
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

def extract_date_from_val(val):
    """Isolates the date part from a string using regex and validates with pd.to_datetime."""
    if pd.isna(val) or str(val).lower() in ['nan', 'n/a', '', 'none']:
        return None
    val = str(val)
    # Search for date pattern: DD-MM-YYYY, DD-Feb-YYYY, YYYY-MM-DD
    match = re.search(r'(\d{1,4}[-/][a-zA-Z0-9]{2,10}[-/]\d{1,4})', val)
    if match:
        date_part = match.group(1)
        dt_obj = pd.to_datetime(date_part, errors='coerce')
        if pd.notnull(dt_obj):
            return dt_obj.strftime("%d-%m-%Y")
    
    # Fallback to direct parse
    dt_obj = pd.to_datetime(val, errors='coerce')
    if pd.notnull(dt_obj):
        return dt_obj.strftime("%d-%m-%Y")
    return None

# --- HELPERS ---
def normalize_branch(name):
    name = str(name).upper().strip()
    # Check for Exact Short Codes first (if they exist as standalone words)
    tokens = set(name.replace('.', ' ').split())
    
    if 'CIVIL' in tokens: return 'CIVIL'
    if 'CSE' in tokens: return 'CSE'
    if 'EEE' in tokens: return 'EEE'
    if 'ECE' in tokens: return 'ECE'
    if 'MECH' in tokens: return 'MECH'
    if 'MCT' in tokens: return 'MCT'
    if 'MECT' in tokens: return 'MCT' # Handle MECT -> MCT mapping
    if 'BIOMED' in tokens: return 'BIOMED'
    if 'IT' in tokens: return 'IT'
    if 'AIDS' in tokens: return 'AIDS'
    if 'CSBS' in tokens: return 'CSBS'
    if 'AIML' in tokens: return 'AIML'
    if 'ACT' in tokens: return 'ACT'
    if 'VLSI' in tokens: return 'VLSI'
    
    # Fuzzy / Substring Matching (Long Names)
    if 'CIVIL' in name: return 'CIVIL'
    if 'COMPUTER SCIENCE AND BUSINESS' in name: return 'CSBS'
    if 'BUSINESS SYSTEM' in name: return 'CSBS'
    if 'DATA SCIENCE' in name: return 'AIDS'
    if 'MACHINE LEARNING' in name: return 'AIML'
    if 'INFORMATION TECH' in name: return 'IT'
    if 'BIOMEDICAL' in name: return 'BIOMED'
    if 'MECHATRONICS' in name: return 'MCT'
    if 'COMMUNICATION' in name: return 'ECE'
    if 'ELECTRICAL' in name: return 'EEE'
    if 'MECHANICAL' in name: return 'MECH'
    if 'COMPUTER SCIENCE' in name: 
        if 'ENGINEERING' in name: return 'CSE'
        return 'CS' # Plain CS
    if 'AGRICULT' in name: return 'ACT'
    return name

year_map = {
    '1': 'I', '1ST': 'I', 'FIRST': 'I', 'I': 'I', 'YEAR 1': 'I', '1 YEAR': 'I',
    '2': 'II', '2ND': 'II', 'SECOND': 'II', 'II': 'II', 'YEAR 2': 'II', '2 YEAR': 'II',
    '3': 'III', '3RD': 'III', 'THIRD': 'III', 'III': 'III', 'YEAR 3': 'III', '3 YEAR': 'III',
    '4': 'IV', '4TH': 'IV', 'FOURTH': 'IV', 'IV': 'IV', 'YEAR 4': 'IV', '4 YEAR': 'IV',
    'CITAR-III': 'CITAR-III'
}

def normalize_year_val(val):
    val = str(val).upper().strip()
    # Broad catch for any CITAR related year labeling
    if val in year_map: return year_map[val]
    if 'SECOND' in val or '2ND' in val: return 'II'
    if 'THIRD' in val or '3RD' in val: return 'III'
    if 'FIRST' in val or '1ST' in val: return 'I'
    if 'FOURTH' in val or '4TH' in val: return 'IV'
    if '2028' in val: return 'II'
    if '2027' in val: return 'III'  # Regular III year
    if 'CITAR' in val: return 'CITAR-III'
    
    if re.search(r'\bII\b', val): return 'II'
    if re.search(r'\bIII\b', val): return 'III'
    if re.search(r'\bI\b', val): return 'I'
    if re.search(r'\bIV\b', val): return 'IV'
    digits = re.findall(r'\d+', val)
    if digits:
        for d in digits:
            if d == '1': return 'I'
            if d == '2': return 'II'
            if d == '3': return 'III'
            if d == '4': return 'IV'
    return val

st.set_page_config(page_title="Result Analysis Tool", layout="wide")

# --- AUTHENTICATION ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        try:
            correct_password = st.secrets.get("password", "cit")
        except:
            correct_password = "cit"

        if hmac.compare_digest(st.session_state["password"], correct_password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.title("🔒 Login")
    st.text_input(
        "Please enter the password to access the Result Analysis Tool", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

st.title("🎓 Office of the Controller of Examinations")
st.header("Skill Rack Result Analysis Automation")

# TABS for Workflow
tab1, tab2 = st.tabs(["📊 Generate New Report", "📜 Report History"])

with tab1:
    # File Uploaders
    # File Uploaders

    st.write("### Upload File(s)")
    uploaded_files = st.file_uploader("Upload 'Result/Usage' Files (for Appeared Count)", type=["xlsx", "xls", "csv"], key="res", accept_multiple_files=True)

    # --- STATIC DATA (HARDCODED) ---
    STATIC_STRENGTH = [
        # Second Year (II)
        {"Branch": "CIVIL", "Year": "II", "Registered_Count": 29},
        {"Branch": "CSE", "Year": "II", "Registered_Count": 1091},
        {"Branch": "EEE", "Year": "II", "Registered_Count": 65},
        {"Branch": "ECE", "Year": "II", "Registered_Count": 267},
        {"Branch": "MECH", "Year": "II", "Registered_Count": 128},
        {"Branch": "MCT", "Year": "II", "Registered_Count": 61},
        {"Branch": "BIOMED", "Year": "II", "Registered_Count": 62},
        {"Branch": "IT", "Year": "II", "Registered_Count": 193},
        {"Branch": "AIDS", "Year": "II", "Registered_Count": 335},
        {"Branch": "CSBS", "Year": "II", "Registered_Count": 67},
        {"Branch": "AIML", "Year": "II", "Registered_Count": 130},
        {"Branch": "CS", "Year": "II", "Registered_Count": 72},
        {"Branch": "ACT", "Year": "II", "Registered_Count": 63},
        {"Branch": "VLSI", "Year": "II", "Registered_Count": 64},
        
        # Third Year (III)
        {"Branch": "CIVIL", "Year": "III", "Registered_Count": 32},
        {"Branch": "CSE", "Year": "III", "Registered_Count": 258},
        {"Branch": "EEE", "Year": "III", "Registered_Count": 63},
        {"Branch": "ECE", "Year": "III", "Registered_Count": 193},
        {"Branch": "MECH", "Year": "III", "Registered_Count": 126},
        {"Branch": "MCT", "Year": "III", "Registered_Count": 61},
        {"Branch": "BIOMED", "Year": "III", "Registered_Count": 63},
        {"Branch": "IT", "Year": "III", "Registered_Count": 193},
        {"Branch": "AIDS", "Year": "III", "Registered_Count": 163},
        {"Branch": "CSBS", "Year": "III", "Registered_Count": 63},
        {"Branch": "AIML", "Year": "III", "Registered_Count": 128},
        {"Branch": "CS", "Year": "III", "Registered_Count": 63},
        {"Branch": "ACT", "Year": "III", "Registered_Count": 60},
        {"Branch": "VLSI", "Year": "III", "Registered_Count": 65},
        
        # CITAR (Third Year Only)
        {"Branch": "CSE", "Year": "CITAR-III", "Registered_Count": 189},
        {"Branch": "AIDS", "Year": "CITAR-III", "Registered_Count": 63},
        {"Branch": "EEE", "Year": "CITAR-III", "Registered_Count": 59},
        {"Branch": "ECE", "Year": "CITAR-III", "Registered_Count": 64}
    ]

    if uploaded_files:
        try:
            # --- USE STATIC DATA FOR REGISTERED COUNTS ---
            registered_counts = pd.DataFrame(STATIC_STRENGTH)

            # --- LOAD RESULT FILES (APPEARED) ---
            all_dfs = []
            seen_names = set()
            processed_files_names = []

            for res_file in uploaded_files:
                if res_file.name in seen_names:
                    st.warning(f"⚠️ duplicate file skipped: {res_file.name}")
                    continue
                
                seen_names.add(res_file.name)
                processed_files_names.append(res_file.name)

                if res_file.name.endswith('.csv'):
                    df = pd.read_csv(res_file)
                else:
                    df = pd.read_excel(res_file)
                
                # Tag with source filename for CITAR detection
                df['Source_Filename'] = res_file.name.lower()
                all_dfs.append(df)
            
            if not all_dfs:
                st.stop()

            # Concatenate all inputs
            df_res = pd.concat(all_dfs, ignore_index=True)

            # Res Column Mapping
            df_res.columns = df_res.columns.str.strip() 
            res_col_map = {
                'Branch': ['branch', 'department', 'dept', 'branch name', 'major', 'discipline'],
                'Year': ['year', 'yr', 'batch', 'year of study', 'study year', 'academic year', 'standard'],
                'Solved count': ['solved count', 'problems solved', 'total solved', 'problems count', 'solved'],
                'Total submissions': ['total submissions', 'total attempts', 'submission count'],
                'Active utilisation': ['active utilisation', 'active utilization', 'active status'],
                'Reg No': ['registration number', 'reg no', 'roll no', 'reg_no', 'student id', 'roll number', 'student registration id', 'reg_id', 'id', 'student_id'],
                'Timestamp': [
                    'timestamp', 'date', 'uploaded at', 'time', 'usage date', 'usage time', 
                    'last login', 'completion date', 'date/time', 'login time', 'submitted on', 
                    'test date', 'created at', 'start time'
                ]
            }
            for standard, variations in res_col_map.items():
                for col in df_res.columns:
                    if col.lower() in variations or col.lower() == standard.lower():
                        df_res.rename(columns={col: standard}, inplace=True)
                        break 
            
            required_cols = ['Branch', 'Year', 'Solved count']
            missing = [col for col in required_cols if col not in df_res.columns]
            
            if missing:
                st.error(f"Result Data missing columns: {missing}")
            else:
                # --- PROCESS DATA ---
                
                # Clean Result Data
                # Handle Merged Cells (Forward Fill)
                df_res['Branch'] = df_res['Branch'].ffill()
                df_res['Year'] = df_res['Year'].ffill()
                
                df_res['Branch'] = df_res['Branch'].fillna('Unknown').astype(str).str.strip().str.upper()
                df_res['Year'] = df_res['Year'].fillna('Unknown').astype(str).str.strip().str.upper()

                # --- REFINED CITAR DETECTION ---
                # Check for explicit "CITAR" labeling in Year column
                mask_yr = df_res['Year'].astype(str).str.upper().str.contains('CITAR', na=False)
                df_res.loc[mask_yr, 'Year'] = 'CITAR-III'
                
                # Registration Number is the definitive student-level authority (Primary Trigger)
                if 'Reg No' in df_res.columns:
                    mask_reg = df_res['Reg No'].astype(str).str.upper().str.contains('CITAR', na=False)
                    df_res.loc[mask_reg, 'Year'] = 'CITAR-III'
                
                # --- DATE EXTRACTION & GROUPING ---
                if 'Timestamp' in df_res.columns:
                    df_res['Derived_Date'] = df_res['Timestamp'].apply(extract_date_from_val)
                else:
                    df_res['Derived_Date'] = "Not Detected in Records"
                
                # Filter out rows where date is missing? No, keep them as "Unknown" if needed
                df_res['Derived_Date'] = df_res['Derived_Date'].fillna("Not Detected in Records")
                
                # --- PROCESS EACH DATE GROUP ---
                unique_dates = df_res['Derived_Date'].unique()
                reports_to_show = [] # List of (date, df, years_text)
                
                # --- AGGREGATE DATA ---
                current_raw_data = [] # List of {date, Branch, Year, Registered, Appeared, Zero, One, Two, Three}
                historical_raw_data = [] # For non-active dates
                
                # 1. Collect from Current Uploads
                for d_str in unique_dates:
                    df_date = df_res[df_res['Derived_Date'] == d_str].copy()
                    df_date['Branch'] = df_date['Branch'].apply(normalize_branch)
                    df_date['Year'] = df_date['Year'].astype(str).replace(r'\.0$', '', regex=True).apply(normalize_year_val)
                    df_date['Solved count'] = pd.to_numeric(df_date['Solved count'], errors='coerce').fillna(0).astype(int)
                    
                    for (branch, year), group in df_date.groupby(['Branch', 'Year']):
                        reg = registered_counts[(registered_counts['Branch'] == branch) & (registered_counts['Year'] == year)]
                        reg_val = int(reg.iloc[0]['Registered_Count']) if not reg.empty else 0
                        current_raw_data.append({
                            'date': d_str, 'Branch': branch, 'Year': year, 
                            'Registered': reg_val, 'Appeared': len(group),
                            'Zero': len(group[group['Solved count'] == 0]),
                            'One': len(group[group['Solved count'] == 1]),
                            'Two': len(group[group['Solved count'] == 2]),
                            'Three': len(group[group['Solved count'] >= 3])
                        })

                # 2. Collect from History (Only for UNRELATED dates)
                hist_meta = database.get_all_reports()
                for _, meta in hist_meta.iterrows():
                    h_date = meta['analysis_date']
                    if not h_date or h_date == "N/A" or h_date in unique_dates: continue
                    h_df = database.get_report_data(meta['id'])
                    if not h_df.empty:
                        raw_h = h_df[~h_df['Branch'].str.contains('TOTAL', na=False)].copy()
                        for _, r in raw_h.iterrows():
                            historical_raw_data.append({
                                'date': h_date, 'Branch': r['Branch'], 'Year': r['Year'],
                                'Registered': int(r['No of Registered Students']),
                                'Appeared': int(r['No of Students Appeared']),
                                'Zero': int(r['Zero Problems Solved']),
                                'One': int(r['One Problem Solved']),
                                'Two': int(r['Two Problems Solved']),
                                'Three': int(r['Three Problems Solved'])
                            })

                # --- GENERATE FINAL REPORTS ---
                all_final_reports = []
                year_sort_map = {"I": 1, "II": 2, "III": 3, "CITAR-III": 4, "IV": 5}
                
                # Helper to process a set of raw data rows for a date
                def generate_report_df(date_str, raw_rows):
                    df_temp = pd.DataFrame(raw_rows)
                    if df_temp.empty: return pd.DataFrame()
                    # Group by Branch/Year to handle if history had duplicates (shouldn't happen but safe)
                    df_temp = df_temp.groupby(['Branch', 'Year']).max().reset_index()
                    
                    final_rows = []
                    grand_total = {"Branch": "OVERALL TOTAL", "Year": "", "No of Registered Students": 0, "No of Students Appeared": 0, "No of Students Absent": 0, "Zero Problems Solved": 0, "One Problem Solved": 0, "Two Problems Solved": 0, "Three Problems Solved": 0}
                    
                    for branch in sorted(df_temp['Branch'].unique()):
                        b_df = df_temp[df_temp['Branch'] == branch].copy()
                        b_df['Year_Sort'] = b_df['Year'].map(lambda x: year_sort_map.get(x, 99))
                        b_df = b_df.sort_values('Year_Sort')
                        
                        for _, r in b_df.iterrows():
                            absent = max(0, r['Registered'] - r['Appeared'])
                            row = {"Branch": r['Branch'], "Year": r['Year'], "No of Registered Students": int(r['Registered']), "No of Students Appeared": int(r['Appeared']), "No of Students Absent": int(absent), "Zero Problems Solved": int(r['Zero']), "One Problem Solved": int(r['One']), "Two Problems Solved": int(r['Two']), "Three Problems Solved": int(r['Three'])}
                            final_rows.append(row)
                            for k in ["No of Registered Students", "No of Students Appeared", "No of Students Absent", "Zero Problems Solved", "One Problem Solved", "Two Problems Solved", "Three Problems Solved"]: 
                                grand_total[k] += row[k]
                        
                        if len(b_df) > 1:
                            b_reg, b_app = b_df['Registered'].sum(), b_df['Appeared'].sum()
                            final_rows.append({"Branch": f"{branch} TOTAL", "Year": "", "No of Registered Students": int(b_reg), "No of Students Appeared": int(b_app), "No of Students Absent": int(max(0, b_reg - b_app)), "Zero Problems Solved": int(b_df['Zero'].sum()), "One Problem Solved": int(b_df['One'].sum()), "Two Problems Solved": int(b_df['Two'].sum()), "Three Problems Solved": int(b_df['Three'].sum())})
                    
                    final_rows.append(grand_total)
                    return pd.DataFrame(final_rows)

                # Process current upload dates
                c_df_temp = pd.DataFrame(current_raw_data)
                for d_str in unique_dates:
                    d_rows = [r for r in current_raw_data if r['date'] == d_str]
                    res_df = generate_report_df(d_str, d_rows)
                    if res_df.empty: continue
                    u_yrs = sorted(list(set([r['Year'] for r in d_rows])))
                    report_obj = {"date": d_str, "df": res_df, "years_text": ", ".join(u_yrs), "is_current": True}
                    all_final_reports.append(report_obj)
                    
                    # Save to DB (Strictly new data for this session)
                    unique_id = f"Upload_{d_str}_{len(uploaded_files)}"
                    if 'last_saved' not in st.session_state: st.session_state.last_saved = set()
                    if unique_id not in st.session_state.last_saved:
                        database.save_report("Manual Upload", "User File", d_str, res_df)
                        st.session_state.last_saved.add(unique_id)
                        st.toast(f"Report for {d_str} saved!", icon="💾")

                # Process historical dates (Only those not in current upload)
                h_df_temp = pd.DataFrame(historical_raw_data)
                if not h_df_temp.empty:
                    for d_str in h_df_temp['date'].unique():
                        d_rows = [r for r in historical_raw_data if r['date'] == d_str]
                        res_df = generate_report_df(d_str, d_rows)
                        if res_df.empty: continue
                        u_yrs = sorted(list(set([r['Year'] for r in d_rows])))
                        all_final_reports.append({"date": d_str, "df": res_df, "years_text": ", ".join(u_yrs), "is_current": False})
                    

                # --- UI DISPLAY ---
                for rep in all_final_reports:
                    if rep['is_current']:
                        st.subheader(f"Generated Analysis Report - Date: {rep['date']}")
                        st.dataframe(rep['df'])
                
                # --- EXCEL GENERATION (All Dates, Chronological) ---
                st.write("### Export Options")
                def sort_rep(r):
                    try: return datetime.strptime(r['date'], "%d-%m-%Y")
                    except: return datetime.min
                all_final_reports.sort(key=sort_rep)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    for rep in all_final_reports:
                        pfx = "Past_" if not rep['is_current'] else ""
                        sheet_name = f"{pfx}{rep['date']}"[:31]
                        rep['df'].to_excel(writer, index=False, sheet_name=sheet_name, startrow=5, header=False)
                        write_formatted_sheet(workbook, writer.sheets[sheet_name], rep['df'], rep['date'], rep['years_text'])

                # Filename from Current
                curr_ds = sorted(list(set([r['date'] for r in all_final_reports if r['is_current']])))
                fn_dt = "_".join(curr_ds).replace("/", "-") if curr_ds else datetime.now().strftime('%d-%m-%Y')

                st.download_button(label="Download Analysis Report", data=output.getvalue(), file_name=f"Skill_Rack_Analysis_{fn_dt}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            st.error(f"An error occurred: {e}")

with tab2:
    st.header("History")
    history_df = database.get_all_reports()
    
    if history_df.empty:
        st.info("No reports generated yet.")
    else:
        # Create a cleaner list for selection
        # Handle cases where analysis_date might be missing for older records
        history_df['analysis_date'] = history_df['analysis_date'].fillna("N/A")
        history_df['display_name'] = (
            history_df['id'].astype(str) + " | " + 
            history_df['timestamp'] + " | " + 
            history_df['analysis_date'] + " | " + 
            history_df['res_filename']
        )
        selection = st.selectbox("Select a past report to view/download", options=history_df['display_name'].tolist())
        
        selected_id = int(selection.split(" | ")[0])
        selected_report = history_df[history_df['id'] == selected_id].iloc[0]
        selected_analysis_date = selected_report['analysis_date']
        
        if st.button("View Report Details"):
            detail_df = database.get_report_data(selected_id)
            if not detail_df.empty:
                st.write(f"### Details for Report #{selected_id}")
                st.dataframe(detail_df)
                
                # --- DOWNLOAD OPTION FOR PAST REPORT ---
                # Quick Excel generation (Simple version for history)
                hist_output = io.BytesIO()
                with pd.ExcelWriter(hist_output, engine='xlsxwriter') as writer:
                    detail_df.to_excel(writer, index=False, sheet_name='Historical Report')
                
                st.download_button(
                    label="Download this Past Report (Excel)",
                    data=hist_output.getvalue(),
                    file_name=f"Result_Analysis_{selected_analysis_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Data not found for this report.")
                
        st.divider()
        st.write("#### Full History Log")
        st.dataframe(history_df[['id', 'timestamp', 'analysis_date', 'res_filename', 'total_students']])