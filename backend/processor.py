import pandas as pd
import re
from datetime import datetime

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

YEAR_MAP = {
    '1': 'I', '1ST': 'I', 'FIRST': 'I', 'I': 'I', 'YEAR 1': 'I', '1 YEAR': 'I',
    '2': 'II', '2ND': 'II', 'SECOND': 'II', 'II': 'II', 'YEAR 2': 'II', '2 YEAR': 'II',
    '3': 'III', '3RD': 'III', 'THIRD': 'III', 'III': 'III', 'YEAR 3': 'III', '3 YEAR': 'III',
    '4': 'IV', '4TH': 'IV', 'FOURTH': 'IV', 'IV': 'IV', 'YEAR 4': 'IV', '4 YEAR': 'IV',
    'CITAR-III': 'CITAR-III'
}

def parse_duration_to_seconds(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'n/a', '', 'none']:
        return 99999999
    val = str(val).strip()
    try:
        parts = list(map(int, val.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        else:
            return 99999999
    except:
         return 99999999

def extract_date_from_val(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'n/a', '', 'none']:
        return None
    val = str(val)
    match = re.search(r'(\d{1,4}[-/][a-zA-Z0-9]{2,10}[-/]\d{1,4})', val)
    if match:
        date_part = match.group(1)
        dt_obj = pd.to_datetime(date_part, errors='coerce')
        if pd.notnull(dt_obj):
            return dt_obj.strftime("%d-%m-%Y")
    dt_obj = pd.to_datetime(val, errors='coerce')
    if pd.notnull(dt_obj):
        return dt_obj.strftime("%d-%m-%Y")
    return None

def normalize_branch(name):
    name = str(name).upper().strip()
    # Replace common separators with space for word boundary matching
    name_clean = name.replace('.', ' ').replace('&', ' ').replace('-', ' ')
    tokens = set(name_clean.split())
    
    # Specific Token Matches
    if 'CIVIL' in tokens: return 'CIVIL'
    if 'CSE' in tokens: return 'CSE'
    if 'EEE' in tokens: return 'EEE'
    if 'ECE' in tokens: return 'ECE'
    if 'MECH' in tokens: return 'MECH'
    if 'MCT' in tokens: return 'MCT'
    if 'MECT' in tokens: return 'MCT'
    if 'BIOMED' in tokens or 'BME' in tokens: return 'BIOMED'
    if 'IT' in tokens: return 'IT'
    if 'AIDS' in tokens or ('AI' in tokens and 'DS' in tokens) or 'AD' in tokens or 'AI' in tokens: return 'AIDS'
    if 'CSBS' in tokens: return 'CSBS'
    if 'AIML' in tokens: return 'AIML'
    if 'ACT' in tokens: return 'ACT'
    if 'VLSI' in tokens: return 'VLSI'
    
    # Full Name / Substring Matches
    name_full = name.replace('.', '').replace('&', ' AND ')
    if 'CIVIL' in name_full: return 'CIVIL'
    if 'COMPUTER SCIENCE' in name_full and 'BUSINESS' in name_full: return 'CSBS'
    if 'BUSINESS SYSTEM' in name_full: return 'CSBS'
    if 'DATA SCIENCE' in name_full or 'AI AND DS' in name_full or 'AI & DS' in name_full: return 'AIDS'
    if 'MACHINE LEARNING' in name_full: return 'AIML'
    if 'INFORMATION TECH' in name_full: return 'IT'
    if 'BIOMEDICAL' in name_full: return 'BIOMED'
    if 'MECHATRONICS' in name_full: return 'MCT'
    if 'COMMUNICATION' in name_full: return 'ECE'
    if 'ELECTRICAL' in name_full: return 'EEE'
    if 'MECHANICAL' in name_full: return 'MECH'
    
    # Handle CS vs CSE carefully
    if 'COMPUTER SCIENCE' in name_full:
        if 'ENGINEERING' in name_full: return 'CSE'
        return 'CS' # Match "CS" in STATIC_STRENGTH if Engineering is not mentioned
    
    if 'AGRICULT' in name_full: return 'ACT'
    return name

def normalize_year_val(val):
    val = str(val).upper().strip()
    if val in YEAR_MAP: return YEAR_MAP[val]
    if 'SECOND' in val or '2ND' in val: return 'II'
    if 'THIRD' in val or '3RD' in val: return 'III'
    if 'FIRST' in val or '1ST' in val: return 'I'
    if 'FOURTH' in val or '4TH' in val: return 'IV'
    if '2028' in val: return 'II'
    if '2027' in val: return 'III'
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

def standardize_columns(df):
    df.columns = df.columns.str.strip()
    for standard, variations in RES_COL_MAP.items():
        candidates = []
        for col in df.columns:
            if col.lower() in variations or col.lower() == standard.lower():
                candidates.append(col)
        if not candidates: continue
        best_col = candidates[0]
        if len(candidates) > 1:
            best_col = max(candidates, key=lambda c: df[c].count())
        if best_col != standard:
             df.rename(columns={best_col: standard}, inplace=True)
        other_candidates = [c for c in candidates if c != best_col and c in df.columns]
        if other_candidates:
            df.drop(columns=other_candidates, inplace=True)
    if 'Reg No' not in df.columns:
        col_map = {c.lower().strip(): c for c in df.columns}
        for norm_col, orig_col in col_map.items():
            if 'reg' in norm_col and 'no' in norm_col:
                df.rename(columns={orig_col: 'Reg No'}, inplace=True)
                break
    return df
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

REGISTERED_COUNTS_DF = pd.DataFrame(STATIC_STRENGTH)

def generate_daily_reports(df_res):
    # Standardize columns has already been called in main.py
    df_res['Branch'] = df_res['Branch'].ffill()
    df_res['Year'] = df_res['Year'].ffill()
    df_res['Branch'] = df_res['Branch'].fillna('Unknown').astype(str).str.strip().str.upper()
    df_res['Year'] = df_res['Year'].fillna('Unknown').astype(str).str.strip().str.upper()

    mask_yr = df_res['Year'].astype(str).str.upper().str.contains('CITAR', na=False)
    df_res.loc[mask_yr, 'Year'] = 'CITAR-III'
    if 'Reg No' in df_res.columns:
        mask_reg = df_res['Reg No'].astype(str).str.upper().str.contains('CITAR', na=False)
        df_res.loc[mask_reg, 'Year'] = 'CITAR-III'

    if 'Timestamp' in df_res.columns:
        df_res['Derived_Date'] = df_res['Timestamp'].apply(extract_date_from_val)
    else:
        df_res['Derived_Date'] = "Not Detected"
    
    df_res['Derived_Date'] = df_res['Derived_Date'].fillna("Not Detected")
    unique_dates = df_res['Derived_Date'].unique()
    
    final_reports = []
    year_sort_map = {"I": 1, "II": 2, "III": 3, "CITAR-III": 4, "IV": 5}

    for d_str in unique_dates:
        df_date = df_res[df_res['Derived_Date'] == d_str].copy()
        df_date['Branch'] = df_date['Branch'].apply(normalize_branch)
        df_date['Year'] = df_date['Year'].astype(str).replace(r'\.0$', '', regex=True).apply(normalize_year_val)
        df_date['Solved count'] = pd.to_numeric(df_date['Solved count'], errors='coerce').fillna(0).astype(int)
        
        raw_rows = []
        for (branch, year), group in df_date.groupby(['Branch', 'Year']):
            reg = REGISTERED_COUNTS_DF[(REGISTERED_COUNTS_DF['Branch'] == branch) & (REGISTERED_COUNTS_DF['Year'] == year)]
            reg_val = int(reg.iloc[0]['Registered_Count']) if not reg.empty else 0
            absent = max(0, reg_val - len(group))
            raw_rows.append({
                "Branch": branch, "Year": year, 
                "No of Registered Students": reg_val, 
                "No of Students Appeared": len(group),
                "No of Students Absent": absent,
                "Zero Problems Solved": len(group[group['Solved count'] == 0]),
                "One Problem Solved": len(group[group['Solved count'] == 1]),
                "Two Problems Solved": len(group[group['Solved count'] == 2]),
                "Three Problems Solved": len(group[group['Solved count'] >= 3])
            })
        
        if not raw_rows: continue
        
        # Build final report DF with totals
        df_temp = pd.DataFrame(raw_rows)
        final_rows = []
        grand_total = {"Branch": "OVERALL TOTAL", "Year": "", "No of Registered Students": 0, "No of Students Appeared": 0, "No of Students Absent": 0, "Zero Problems Solved": 0, "One Problem Solved": 0, "Two Problems Solved": 0, "Three Problems Solved": 0}
        
        for branch in sorted(df_temp['Branch'].unique()):
            b_df = df_temp[df_temp['Branch'] == branch].copy()
            b_df['Year_Sort'] = b_df['Year'].map(lambda x: year_sort_map.get(x, 99))
            b_df = b_df.sort_values('Year_Sort')
            
            for _, r in b_df.iterrows():
                final_rows.append(r.to_dict())
                for k in grand_total.keys():
                    if k not in ["Branch", "Year"]: grand_total[k] += r[k]
            
            if len(b_df) > 1:
                final_rows.append({
                    "Branch": f"{branch} TOTAL", "Year": "", 
                    "No of Registered Students": int(b_df['No of Registered Students'].sum()),
                    "No of Students Appeared": int(b_df['No of Students Appeared'].sum()),
                    "No of Students Absent": int(b_df['No of Students Absent'].sum()),
                    "Zero Problems Solved": int(b_df['Zero Problems Solved'].sum()),
                    "One Problem Solved": int(b_df['One Problem Solved'].sum()),
                    "Two Problems Solved": int(b_df['Two Problems Solved'].sum()),
                    "Three Problems Solved": int(b_df['Three Problems Solved'].sum())
                })
        
        final_rows.append(grand_total)
        u_yrs = sorted(list(set(df_temp['Year'])))
        final_reports.append({
            "date": d_str, 
            "data": final_rows, 
            "years_text": ", ".join(u_yrs)
        })

    return final_reports

def generate_weekly_report(df_res):
    df_weekly = df_res.copy()
    df_weekly['Branch'] = df_weekly['Branch'].apply(normalize_branch)
    df_weekly['Year'] = df_weekly['Year'].astype(str).replace(r'\.0$', '', regex=True).apply(normalize_year_val)
    df_weekly['Solved count'] = pd.to_numeric(df_weekly['Solved count'], errors='coerce').fillna(0).astype(int)
    
    if 'Timestamp' in df_weekly.columns:
        df_weekly['Derived_Date'] = df_weekly['Timestamp'].apply(extract_date_from_val)
    else:
        df_weekly['Derived_Date'] = "Unknown"
    
    if 'Total submissions' not in df_weekly.columns:
        df_weekly['Total submissions'] = 0
    if 'Active utilisation' not in df_weekly.columns:
        df_weekly['Active utilisation'] = '00:00:00'
    
    df_weekly['Active_Secs_Agg'] = df_weekly['Active utilisation'].apply(parse_duration_to_seconds).replace(99999999, 0)
    
    has_reg = 'Reg No' in df_weekly.columns
    id_col = 'Reg No' if has_reg else 'Name'

    # Student-Day Level
    daily_student = df_weekly.groupby([id_col, 'Derived_Date']).agg({
        'Solved count': 'max',
        'Total submissions': 'max',
        'Active_Secs_Agg': 'max',
        'Branch': 'first',
        'Year': 'first',
        'Name': 'first' if has_reg else 'last'
    }).reset_index()
    
    # Weekly Aggregation
    weekly_grouped = daily_student.groupby(id_col).agg({
        'Derived_Date': 'nunique',
        'Solved count': 'sum',
        'Total submissions': 'sum',
        'Active_Secs_Agg': 'sum',
        'Branch': 'first',
        'Year': 'first',
        'Name': 'first' if has_reg else 'last'
    }).reset_index()
    
    weekly_grouped.columns = [id_col, 'Days Appeared', 'Total Solved', 'Total Submissions', 'Active_Secs_Total', 'Branch', 'Year', 'Name']
    
    # Sorting: Solved (Desc), Submissions (Asc)
    sorted_weekly = weekly_grouped.sort_values(
        by=['Total Solved', 'Total Submissions'],
        ascending=[False, True]
    ).reset_index(drop=True)

    return sorted_weekly.to_dict('records')

def get_top_performers(df, top_n=50):
    """
    Unified ranking logic for the API.
    """
    if df.empty:
        return []
    
    # Sort: Solved (Desc), Active Util (Asc), Submissions (Asc)
    # Note: We need to ensure columns are standardized and durations are parsed
    df_calc = df.copy()
    
    # Ensure columns exist or map from alternatives
    if 'Solved count' not in df_calc.columns and 'Total Solved' in df_calc.columns:
        df_calc['Solved count'] = df_calc['Total Solved']
    
    if 'Total submissions' not in df_calc.columns and 'Total Submissions' in df_calc.columns:
        df_calc['Total submissions'] = df_calc['Total Submissions']

    # Default to 0 if still missing
    if 'Solved count' not in df_calc.columns: df_calc['Solved count'] = 0
    if 'Total submissions' not in df_calc.columns: df_calc['Total submissions'] = 0

    # Ensure numeric
    df_calc['Solved count'] = pd.to_numeric(df_calc['Solved count'], errors='coerce').fillna(0)
    df_calc['Total submissions'] = pd.to_numeric(df_calc['Total submissions'], errors='coerce').fillna(0)
    
    # Parse duration
    if 'Active utilisation' in df_calc.columns:
        df_calc['Active_Secs'] = df_calc['Active utilisation'].apply(parse_duration_to_seconds)
    elif 'Active_Secs_Total' in df_calc.columns:
        df_calc['Active_Secs'] = df_calc['Active_Secs_Total']
    else:
        df_calc['Active_Secs'] = 99999999
        
    ranked = df_calc.sort_values(
        by=['Solved count', 'Active_Secs', 'Total submissions'],
        ascending=[False, True, True]
    ).head(top_n).reset_index(drop=True)
    
    return ranked.to_dict('records')
