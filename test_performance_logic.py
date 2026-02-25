import pandas as pd
import sys
import os

# Add current directory to path to import app (if possible, but we'll mock parse_duration_to_seconds)
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

def get_top_performers_df(student_df, top_n=50):
    if student_df.empty:
        return pd.DataFrame()
    
    df = student_df.copy()
    df['Solved count'] = pd.to_numeric(df['Solved count'], errors='coerce').fillna(0)
    df['Total submissions'] = pd.to_numeric(df['Total submissions'], errors='coerce').fillna(0)
    df['Active utilisation_seconds'] = df['Active utilisation'].apply(parse_duration_to_seconds)
    
    ranked = df.sort_values(
        by=['Solved count', 'Active utilisation_seconds', 'Total submissions'],
        ascending=[False, True, True]
    ).head(top_n).reset_index(drop=True)
    
    return ranked

# Test Case
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David'],
    'Solved count': [10, 10, 5, 12],
    'Total submissions': [20, 15, 10, 30],
    'Active utilisation': ['01:00:00', '00:30:00', '00:10:00', '02:00:00'],
    'Branch': ['CSE', 'CSE', 'ECE', 'CSE']
}
df = pd.DataFrame(data)

print("--- Mock Data ---")
print(df)

print("\n--- Top Performers (Overall) ---")
top_overall = get_top_performers_df(df, 2)
print(top_overall)

# Expected: David (12 solved), Bob (10 solved, 30 min util), Alice (10 solved, 1 hour util)
# Top 2 should be David, Bob

if top_overall.iloc[0]['Name'] == 'David' and top_overall.iloc[1]['Name'] == 'Bob':
    print("\nSUCCESS: Overall ranking correct.")
else:
    print("\nFAILURE: Overall ranking incorrect.")

print("\n--- Top Performers (CSE) ---")
cse_df = df[df['Branch'] == 'CSE']
top_cse = get_top_performers_df(cse_df, 2)
print(top_cse)

if top_cse.iloc[0]['Name'] == 'David' and top_cse.iloc[1]['Name'] == 'Bob':
    print("\nSUCCESS: CSE ranking correct.")
else:
    print("\nFAILURE: CSE ranking incorrect.")
