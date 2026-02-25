import pandas as pd
import re

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
    if 'AIDS' in tokens or ('AI' in tokens and ('DS' in tokens or 'DS' in tokens)) or 'AD' in tokens: return 'AIDS'
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
        return 'CS' # Match "CS" in STATIC_STRENGTH
    
    if 'AGRICULT' in name_full: return 'ACT'
    return name

test_cases = [
    ("AI", "AIDS"),
    ("AIDS", "AIDS"),
    ("AD", "AIDS"),
    ("AI & DS", "AIDS"),
    ("AI&DS", "AIDS"),
    ("ARTIFICIAL INTELLIGENCE AND DATA SCIENCE", "AIDS"),
    ("BME", "BIOMED"),
    ("BIOMEDICAL ENGINEERING", "BIOMED"),
    ("CS", "CS"),
    ("COMPUTER SCIENCE", "CS"),
    ("COMPUTER SCIENCE AND ENGINEERING", "CSE"),
    ("CSE", "CSE"),
    ("ECE", "ECE"),
    ("ELECTRONICS AND COMMUNICATION", "ECE"),
    ("IT", "IT"),
    ("INFORMATION TECHNOLOGY", "IT"),
]

print(f"{'Input':<40} | {'Expected':<10} | {'Actual':<10} | {'Result'}")
print("-" * 80)
for inp, exp in test_cases:
    act = normalize_branch(inp)
    res = "PASS" if act == exp else "FAIL"
    print(f"{inp:<40} | {exp:<10} | {act:<10} | {res}")
