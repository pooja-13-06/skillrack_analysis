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

def get_top_performers_df(student_df, top_n=50):
    """
    Core logic to sort and filter top performers.
    """
    if student_df.empty:
        return pd.DataFrame()
    
    df = student_df.copy()
    df['Solved count'] = pd.to_numeric(df['Solved count'], errors='coerce').fillna(0)
    df['Total submissions'] = pd.to_numeric(df['Total submissions'], errors='coerce').fillna(0)
    df['Active utilisation_seconds'] = df['Active utilisation'].apply(parse_duration_to_seconds)
    
    # Sort: Solved count (desc), Active utilisation (asc), Total submissions (asc)
    ranked = df.sort_values(
        by=['Solved count', 'Active utilisation_seconds', 'Total submissions'],
        ascending=[False, True, True]
    ).head(top_n).reset_index(drop=True)
    
    return ranked

def write_student_rankings(workbook, worksheet, student_df, top_n, start_row_offset):
    """
    Write student performance rankings to the worksheet below the summary.
    Returns the number of rows written.
    """
    if student_df.empty:
        return 0
    
    # Formats
    section_header_fmt = workbook.add_format({
        'bold': True, 'font_size': 12, 'bg_color': '#4472C4', 
        'font_color': 'white', 'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    perf_header_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#B4C7E7', 'border': 1, 
        'align': 'center', 'valign': 'vcenter'
    })
    rank_fmt = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'bold': True
    })
    data_fmt = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    gold_fmt = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 
        'bg_color': '#FFD700', 'bold': True
    })
    silver_fmt = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 
        'bg_color': '#C0C0C0', 'bold': True
    })
    bronze_fmt = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 
        'bg_color': '#CD7F32', 'bold': True
    })
    
    def get_rank_fmt(rank):
        if rank == 1: return gold_fmt
        if rank == 2: return silver_fmt
        if rank == 3: return bronze_fmt
        return rank_fmt

    def safe_get(row_data, col, default='N/A'):
        """Safely get a value from a pandas Series by column name."""
        return row_data[col] if col in row_data.index else default

    def write_student_row(ws, row_idx, rank, row_data):
        ws.write(row_idx, 0, rank, get_rank_fmt(rank))
        ws.write(row_idx, 1, str(safe_get(row_data, 'Reg No')), data_fmt)
        ws.write(row_idx, 2, str(safe_get(row_data, 'Name')), data_fmt)
        ws.write(row_idx, 3, str(safe_get(row_data, 'Branch')), data_fmt)
        ws.write(row_idx, 4, str(safe_get(row_data, 'Year')), data_fmt)
        ws.write(row_idx, 5, int(safe_get(row_data, 'Solved count', 0)), data_fmt)
        ws.write(row_idx, 6, int(safe_get(row_data, 'Total submissions', 0)), data_fmt)
        ws.write(row_idx, 7, str(safe_get(row_data, 'Active utilisation', 'N/A')), data_fmt)

    headers = ["Rank", "Reg No", "Name", "Branch", "Year", "Problems Solved", "Submissions", "Active Util"]
    current_row = start_row_offset
    
    def write_section(ws, section_df, title, start):
        row = start
        ws.merge_range(row, 0, row, 7, title, section_header_fmt)
        row += 1
        for col, header in enumerate(headers):
            ws.write(row, col, header, perf_header_fmt)
        row += 1
        
        ranked = get_top_performers_df(section_df, top_n)
        
        for idx, r in ranked.iterrows():
            write_student_row(ws, row, idx + 1, r)
            row += 1
        return row + 2  # gap

    # --- OVERALL ---
    current_row = write_section(worksheet, student_df, "OVERALL TOP PERFORMERS", current_row)
    
    # --- BRANCH-WISE ---
    for branch in sorted(df['Branch'].unique()):
        branch_df = df[df['Branch'] == branch]
        current_row = write_section(worksheet, branch_df, f"{branch} - TOP PERFORMERS", current_row)
    
    # Set column widths
    worksheet.set_column('A:A', 8)
    worksheet.set_column('B:B', 18)
    worksheet.set_column('C:C', 25)
    worksheet.set_column('D:D', 12)
    worksheet.set_column('E:E', 10)
    worksheet.set_column('F:H', 15)
    
    return current_row - start_row_offset

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
    if 'AI' in tokens: return 'AIDS'
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

# Column Mapping Definition
RES_COL_MAP = {
    'Reg No': ['regn num', 'regn no', 'reg no', 'registration number', 'regn_no', 'roll no', 'reg_no', 'student id', 'roll number', 'student registration id', 'reg_id', 'id', 'student_id'],
    'Branch': ['branch', 'department', 'dept', 'branch name', 'major', 'discipline'],
    'Year': ['year', 'yr', 'batch', 'year of study', 'study year', 'academic year', 'standard'],
    'Solved count': ['solved count', 'problems solved', 'total solved', 'problems count', 'solved'],
    'Total submissions': ['total submissions', 'total attempts', 'submission count'],
    'Active utilisation': ['active utilisation', 'active utilization', 'active status', 'duration', 'active duration', 'active time', 'total active time', 'usage duration', 'time spent'],
    'Name': ['name', 'student name', 'full name', 'student_name', 'fullname'],
    'Timestamp': [
        'timestamp', 'date', 'uploaded at', 'time', 'usage date', 'usage time', 
        'last login', 'completion date', 'date/time', 'login time', 'submitted on', 
        'test date', 'created at', 'start time'
    ]
}

def parse_duration_to_seconds(val):
    """Utility to convert HH:MM:SS or HH:MM duration strings to seconds."""
    if pd.isna(val) or str(val).lower() in ['nan', 'n/a', '', 'none']:
        return 99999999 # Treat NaNs as very large time (bottom of list)
    val = str(val).strip()
    try:
        # Handle HH:MM:SS
        parts = list(map(int, val.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        else:
            return 99999999
    except:
         return 99999999

def standardize_columns(df):
    """Standardize column names for a single dataframe, handling collisions."""
    df.columns = df.columns.str.strip()
    
    # Apply mapping
    for standard, variations in RES_COL_MAP.items():
        # Find all columns that match this standard key (including itself)
        candidates = []
        for col in df.columns:
            if col.lower() in variations or col.lower() == standard.lower():
                candidates.append(col)
        
        if not candidates:
            continue
            
        # If multiple candidates exist (e.g. 'Reg No' is empty, 'Regn No' is full), pick the best one
        best_col = candidates[0]
        if len(candidates) > 1:
            # Pick the one with the most non-null values
            best_col = max(candidates, key=lambda c: df[c].count())
        
        # Rename the best candidate to standard
        if best_col != standard:
             df.rename(columns={best_col: standard}, inplace=True)
        
        # Drop other candidates to avoid confusion (if they still exist after rename)
        other_candidates = [c for c in candidates if c != best_col and c in df.columns]
        if other_candidates:
            df.drop(columns=other_candidates, inplace=True)

    # Fallback for Reg No specifically if missed - GREEDY SEARCH
    if 'Reg No' not in df.columns:
        col_map = {c.lower().strip(): c for c in df.columns}
        for norm_col, orig_col in col_map.items():
            if 'reg' in norm_col and 'no' in norm_col:
                df.rename(columns={orig_col: 'Reg No'}, inplace=True)
                break
    return df

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
                
                # Tag with source filename and standardize columns IMMEDIATELY
                df['Source_Filename'] = res_file.name.lower()
                df = standardize_columns(df)
                
                all_dfs.append(df)
            
            if not all_dfs:
                st.stop()

            # Concatenate all inputs
            df_res = pd.concat(all_dfs, ignore_index=True)
            
            # --- OLD MAPPING LOGIC REMOVED FROM HERE ---
            
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
                    
                    # Extract student-level data for this date
                    student_data = df_res[df_res['Derived_Date'] == d_str].copy()
                    student_data['Branch'] = student_data['Branch'].apply(normalize_branch)
                    student_data['Year'] = student_data['Year'].astype(str).replace(r'\.0$', '', regex=True).apply(normalize_year_val)
                    student_data['Solved count'] = pd.to_numeric(student_data['Solved count'], errors='coerce').fillna(0).astype(int)
                    student_data['Total submissions'] = pd.to_numeric(student_data['Total submissions'], errors='coerce').fillna(0).astype(int)
                    if 'Active utilisation' not in student_data.columns:
                        student_data['Active utilisation'] = 'N/A'
                    else:
                        student_data['Active utilisation'] = student_data['Active utilisation'].fillna('N/A')
                    
                    report_obj = {"date": d_str, "df": res_df, "years_text": ", ".join(u_yrs), "is_current": True, "student_data": student_data}
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
                        all_final_reports.append({"date": d_str, "df": res_df, "years_text": ", ".join(u_yrs), "is_current": False, "student_data": pd.DataFrame()})
                    

                # --- UI DISPLAY ---
                # for rep in all_final_reports:
                #     if rep['is_current']:
                #         st.subheader(f"Generated Analysis Report - Date: {rep['date']}")
                #         st.dataframe(rep['df'])
                
                
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

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Analysis Report",
                        data=output.getvalue(),
                        file_name=f"Skill_Rack_Analysis_{fn_dt}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                with col2:
                    if st.button("🏆 Generate Performance Analysis"):
                        st.session_state['show_perf_input'] = True
                    
                    if st.session_state.get('show_perf_input', False):
                        # Extract all available departments from current reports
                        available_depts = set()
                        for rep in all_final_reports:
                            if rep['is_current'] and not rep.get('student_data', pd.DataFrame()).empty:
                                available_depts.update(rep['student_data']['Branch'].unique())
                        
                        available_depts = sorted(list(available_depts))
                        
                        top_n_students = st.number_input(
                            "How many top students to display?",
                            min_value=10, max_value=500, value=50, step=10,
                            key="top_n_input"
                        )
                        
                        selected_depts = st.multiselect(
                            "Select Departments to Generate Report For:",
                            options=["OVERALL"] + available_depts,
                            default=["OVERALL"],
                            key="dept_select"
                        )
                        
                        if st.button("📊 Confirm & Generate", key="confirm_perf"):
                            all_student_data = [] # Just for check
                            for rep in all_final_reports:
                                if rep['is_current'] and not rep.get('student_data', pd.DataFrame()).empty:
                                    all_student_data.append(rep['student_data'])
                            
                            if all_student_data:
                                perf_output = io.BytesIO()
                                with pd.ExcelWriter(perf_output, engine='xlsxwriter') as perf_writer:
                                    perf_wb = perf_writer.book
                                    
                                    for rep in all_final_reports:
                                        if not rep['is_current'] or rep.get('student_data', pd.DataFrame()).empty:
                                            continue
                                        
                                        student_df = rep['student_data']
                                        
                                        # Iterate through selections
                                        for sel in selected_depts:
                                            if sel == "OVERALL":
                                                # Normal behavior: All students + Overall Ranking
                                                perf_sheet_name = f"Perf_ALL_{rep['date']}"[:31]
                                                pd.DataFrame([[]]).to_excel(perf_writer, index=False, sheet_name=perf_sheet_name, header=False)
                                                ws = perf_writer.sheets[perf_sheet_name]
                                                write_student_rankings(perf_wb, ws, student_df, int(top_n_students), 0)
                                            else:
                                                # Specific Dept: Filtered Data, Only that dept listing
                                                dept_df = student_df[student_df['Branch'] == sel]
                                                if not dept_df.empty:
                                                    perf_sheet_name = f"Perf_{sel}_{rep['date']}"[:31]
                                                    pd.DataFrame([[]]).to_excel(perf_writer, index=False, sheet_name=perf_sheet_name, header=False)
                                                    ws = perf_writer.sheets[perf_sheet_name]
                                                    write_student_rankings(perf_wb, ws, dept_df, int(top_n_students), 0)
                                
                                st.download_button(
                                    label="📥 Download Performance Analysis",
                                    data=perf_output.getvalue(),
                                    file_name=f"Performance_Analysis_{fn_dt}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="perf_download"
                                )
                                st.session_state['show_perf_input'] = False
                            else:
                                st.warning("No student data available for performance analysis.")
                
                # --- LIVE PERFORMANCE DASHBOARD ---
                st.divider()
                st.header("🏆 Live Performance Dashboard")
                
                # Collect student data from all current reports
                all_current_student_data = pd.concat([
                    rep['student_data'] for rep in all_final_reports 
                    if rep['is_current'] and not rep.get('student_data', pd.DataFrame()).empty
                ], ignore_index=True) if any(
                    rep['is_current'] and not rep.get('student_data', pd.DataFrame()).empty 
                    for rep in all_final_reports
                ) else pd.DataFrame()

                if not all_current_student_data.empty:
                    p_col1, p_col2, p_col3 = st.columns([1, 1, 1])
                    with p_col1:
                        view_mode = st.radio("Select View Mode", ["Overall", "Department-wise"], horizontal=True)
                    
                    available_depts = sorted(all_current_student_data['Branch'].unique().tolist())
                    
                    selected_view_dept = "OVERALL"
                    if view_mode == "Department-wise":
                        with p_col2:
                            selected_view_dept = st.selectbox("Select Department", available_depts)
                    
                    with p_col3:
                        top_n_live = st.slider("Show Top N Students", 5, 100, 20)
                    
                    # Filter and Display
                    if selected_view_dept == "OVERALL":
                        display_df = all_current_student_data
                        title = f"Top {top_n_live} Performers - Overall"
                    else:
                        display_df = all_current_student_data[all_current_student_data['Branch'] == selected_view_dept]
                        title = f"Top {top_n_live} Performers - {selected_view_dept}"
                    
                    ranked_live = get_top_performers_df(display_df, top_n_live)
                    
                    if not ranked_live.empty:
                        st.subheader(title)
                        # Add Rank column for display
                        ranked_live.insert(0, 'Rank', range(1, len(ranked_live) + 1))
                        
                        # Select relevant columns for UI display
                        ui_cols = ['Rank', 'Reg No', 'Name', 'Branch', 'Year', 'Solved count', 'Total submissions', 'Active utilisation']
                        st.dataframe(ranked_live[ui_cols], use_container_width=True, hide_index=True)
                        
                        # Visual chart
                        st.write("#### Problems Solved Visualization")
                        st.bar_chart(ranked_live.set_index('Name')['Solved count'])
                    else:
                        st.info("No data found for the selected criteria.")
                else:
                    st.info("Upload files to see the live performance dashboard.")
                
                with col2:
                    if st.button("📊 Show Aggregated Overall Performance"):
                        st.session_state['show_weekly_analysis'] = True
                
                if st.session_state.get('show_weekly_analysis', False):
                    st.divider()
                    st.subheader("📅 Aggregated Overall Performance Analysis")
                    
                    # --- AGGREGATION LOGIC ---
                    df_agg = df_res.copy()
                    df_agg['Branch'] = df_agg['Branch'].apply(normalize_branch)
                    df_agg['Year'] = df_agg['Year'].astype(str).replace(r'\.0$', '', regex=True).apply(normalize_year_val)
                    df_agg['Solved count'] = pd.to_numeric(df_agg['Solved count'], errors='coerce').fillna(0).astype(int)
                    
                    if 'Timestamp' in df_agg.columns:
                        df_agg['Derived_Date'] = df_agg['Timestamp'].apply(extract_date_from_val)
                    else:
                        df_agg['Derived_Date'] = "Unknown"
                    
                    if 'Total submissions' not in df_agg.columns:
                        df_agg['Total submissions'] = 0
                    if 'Active utilisation' not in df_agg.columns:
                        df_agg['Active utilisation'] = '00:00:00'
                    
                    df_agg['Active utilisation_seconds'] = df_agg['Active utilisation'].apply(parse_duration_to_seconds)
                    df_agg['Active_Secs_Agg'] = df_agg['Active utilisation_seconds'].replace(99999999, 0)
                    
                    has_reg = 'Reg No' in df_agg.columns
                    id_col = 'Reg No' if has_reg else 'Name'

                    # Clean Date Grouping (Student-Day level)
                    daily_student = df_agg.groupby([id_col, 'Derived_Date']).agg({
                        'Solved count': 'max',
                        'Total submissions': 'max',
                        'Active_Secs_Agg': 'max', 
                        'Branch': 'first',
                        'Year': 'first',
                        'Name': 'first' if has_reg else 'last'
                    }).reset_index()
                    
                    # Aggregation across all files
                    aggregated_grouped = daily_student.groupby(id_col).agg({
                        'Derived_Date': 'nunique',
                        'Solved count': 'sum',
                        'Total submissions': 'sum',
                        'Active_Secs_Agg': 'sum', 
                        'Branch': 'first',
                        'Year': 'first',
                        'Name': 'first' if has_reg else 'last'
                    }).reset_index()
                    
                    # Formatting
                    def format_seconds_to_hhmmss(s):
                        if s <= 0: return "00:00:00"
                        h = s // 3600
                        m = (s % 3600) // 60
                        s = s % 60
                        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

                    aggregated_grouped['Total Active Util'] = aggregated_grouped['Active_Secs_Agg'].apply(format_seconds_to_hhmmss)
                    aggregated_grouped.columns = [id_col, 'Days Appeared', 'Total Solved', 'Total Submissions', 'Active_Secs_Total', 'Branch', 'Year', 'Name', 'Total Active Util']
                    
                    # --- UI CONTROLS FOR AGGREGATED VIEW ---
                    a_col1, a_col2, a_col3 = st.columns([1, 1, 1])
                    with a_col1:
                        agg_view_mode = st.radio("Agg View Mode", ["Overall", "Department-wise"], horizontal=True, key="agg_mode")
                    
                    available_depts_agg = sorted(aggregated_grouped['Branch'].unique().tolist())
                    
                    selected_agg_dept = "OVERALL"
                    if agg_view_mode == "Department-wise":
                        with a_col2:
                            selected_agg_dept = st.selectbox("Select Department", available_depts_agg, key="agg_dept_sel")
                    
                    with a_col3:
                        top_n_agg = st.slider("Show Top N Students", 10, 500, 50, key="agg_slider")

                    # Filter
                    if selected_agg_dept == "OVERALL":
                        df_to_display = aggregated_grouped
                    else:
                        df_to_display = aggregated_grouped[aggregated_grouped['Branch'] == selected_agg_dept]

                    # Sort: Total Solved (Desc) then Total Submissions (Asc)
                    sorted_agg = df_to_display.sort_values(
                        by=['Total Solved', 'Total Submissions'],
                        ascending=[False, True]
                    ).head(top_n_agg).reset_index(drop=True)
                    
                    # Add Rank
                    sorted_agg.insert(0, 'Rank', range(1, len(sorted_agg) + 1))

                    display_cols = ['Rank', id_col, 'Name', 'Branch', 'Year', 'Days Appeared', 'Total Solved', 'Total Submissions', 'Total Active Util']
                    st.dataframe(sorted_agg[display_cols], use_container_width=True, hide_index=True)
                    
                    # Visualization
                    st.write("#### Aggregated Problems Solved Visualization")
                    st.bar_chart(sorted_agg.set_index('Name')['Total Solved'])
                    
                    st.divider()
                    
                    # Export
                    ag_output = io.BytesIO()
                    with pd.ExcelWriter(ag_output, engine='xlsxwriter') as ag_writer:
                        sorted_agg[display_cols].to_excel(ag_writer, index=False, sheet_name='Aggregated Overall Report')
                    
                    st.download_button(
                        label="📥 Download Aggregated Overall Report (Excel)",
                        data=ag_output.getvalue(),
                        file_name=f"Aggregated_Overall_Analysis_{fn_dt}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    if st.button("Close Aggregated View"):
                        st.session_state['show_weekly_analysis'] = False
                        st.rerun()


        except Exception as e:
            import traceback
            st.error(f"An error occurred: {e}")
            st.code(traceback.format_exc())

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

