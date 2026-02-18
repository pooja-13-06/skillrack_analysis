import pandas as pd
import io

# Mocking the logic found in app.py

# Column Mapping Definition (Copied from app.py)
res_col_map = {
    'Reg No': ['regn no', 'reg no', 'registration number', 'regn_no', 'roll no', 'reg_no', 'student id', 'roll number', 'student registration id', 'reg_id', 'id', 'student_id'],
    'Branch': ['branch', 'department', 'dept', 'branch name', 'major', 'discipline'],
    'Year': ['year', 'yr', 'batch', 'year of study', 'study year', 'academic year', 'standard'],
    'Solved count': ['solved count', 'problems solved', 'total solved', 'problems count', 'solved'],
    'Total submissions': ['total submissions', 'total attempts', 'submission count'],
    'Active utilisation': ['active utilisation', 'active utilization', 'active status'],
    'Name': ['name', 'student name', 'full name', 'student_name', 'fullname'],
    'Timestamp': [
        'timestamp', 'date', 'uploaded at', 'time', 'usage date', 'usage time', 
        'last login', 'completion date', 'date/time', 'login time', 'submitted on', 
        'test date', 'created at', 'start time'
    ]
}

def standardize_columns(df):
    """Standardize column names for a single dataframe."""
    df.columns = df.columns.str.strip()
    
    # Apply mapping
    for standard, variations in res_col_map.items():
        for col in df.columns:
            if col.lower() in variations or col.lower() == standard.lower():
                if standard not in df.columns: # Avoid overwriting if matches standard
                    df.rename(columns={col: standard}, inplace=True)
                elif col != standard: 
                    pass

    # Fallback for Reg No specifically if missed - GREEDY SEARCH
    if 'Reg No' not in df.columns:
        col_map = {c.lower().strip(): c for c in df.columns}
        for norm_col, orig_col in col_map.items():
            if 'reg' in norm_col and 'no' in norm_col:
                df.rename(columns={orig_col: 'Reg No'}, inplace=True)
                break
    return df

# Test Case
print("--- Starting Test ---")

# File 1: Uses "Reg No"
data1 = {
    "Reg No": ["1", "2"],
    "Branch": ["CSE", "ECE"],
    "Year": ["I", "II"],
    "Solved count": [10, 20]
}
df1 = pd.DataFrame(data1)
print(f"DF1 Columns (Original): {df1.columns.tolist()}")
df1 = standardize_columns(df1)
print(f"DF1 Columns (Standardized): {df1.columns.tolist()}")

# File 2: Uses "Regn No"
data2 = {
    "Regn No": ["3", "4"],
    "Branch": ["MECH", "IT"],
    "Year": ["III", "IV"],
    "Solved count": [30, 40]
}
df2 = pd.DataFrame(data2)
print(f"DF2 Columns (Original): {df2.columns.tolist()}")
df2 = standardize_columns(df2)
print(f"DF2 Columns (Standardized): {df2.columns.tolist()}")

# Concatenation
all_dfs = [df1, df2]
df_res = pd.concat(all_dfs, ignore_index=True)

print("\n--- Resulting DataFrame ---")
print(df_res)
print(f"Final Columns: {df_res.columns.tolist()}")

if "Reg No" in df_res.columns and "Regn No" not in df_res.columns:
    print("\nSUCCESS: 'Reg No' is present and 'Regn No' is merged/absent.")
    if df_res['Reg No'].isna().sum() == 0:
         print("SUCCESS: No N/A values in 'Reg No'.")
    else:
         print("FAILURE: N/A values found in 'Reg No'.")
         print(df_res[df_res['Reg No'].isna()])
else:
    print("\nFAILURE: Column merging incorrect.")
