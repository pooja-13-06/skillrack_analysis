import sqlite3
import pandas as pd
from datetime import datetime
import os

# --- DATABASE CONFIG ---
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        timestamp TEXT, 
        ref_filename TEXT, 
        res_filename TEXT, 
        analysis_date TEXT, 
        total_students INTEGER
    )''')
    
    # Simple Migration for SQLite
    try:
        c.execute("ALTER TABLE reports ADD COLUMN analysis_date TEXT")
    except:
        pass
        
    c.execute('''CREATE TABLE IF NOT EXISTS report_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        report_id INTEGER, 
        branch TEXT, 
        year TEXT, 
        registered INTEGER, 
        appeared INTEGER, 
        absent INTEGER, 
        zero_solved INTEGER, 
        one_solved INTEGER, 
        two_solved INTEGER, 
        three_solved INTEGER,
        FOREIGN KEY(report_id) REFERENCES reports(id)
    )''')
    conn.commit()
    conn.close()

def save_report(ref_filename, res_filename, analysis_date, final_df):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_row = final_df[final_df['Branch'] == 'OVERALL TOTAL']
    total_students = int(total_row.iloc[0]['No of Registered Students']) if not total_row.empty else 0

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO reports (timestamp, ref_filename, res_filename, analysis_date, total_students) VALUES (?, ?, ?, ?, ?)", 
              (timestamp, ref_filename, res_filename, analysis_date, total_students))
    report_id = c.lastrowid
    
    for _, row in final_df.iterrows():
        c.execute("""INSERT INTO report_data (report_id, branch, year, registered, appeared, absent, zero_solved, one_solved, two_solved, three_solved) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (report_id, row['Branch'], row['Year'], int(row['No of Registered Students']), 
                  int(row['No of Students Appeared']), int(row['No of Students Absent']), 
                  int(row['Zero Problems Solved']), int(row['One Problem Solved']), 
                  int(row['Two Problems Solved']), int(row['Three Problems Solved'])))
    conn.commit()
    conn.close()
    return report_id

def get_all_reports():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM reports ORDER BY id DESC", conn)
    conn.close()
    return df.to_dict('records')

def get_report_data(report_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM report_data WHERE report_id = ?", conn, params=(report_id,))
    conn.close()
    
    if df.empty: return []
    
    df = df.drop(columns=['id', 'report_id'])
    rename_map = {
        'branch': 'Branch', 'year': 'Year', 'registered': 'No of Registered Students',
        'appeared': 'No of Students Appeared', 'absent': 'No of Students Absent',
        'zero_solved': 'Zero Problems Solved', 'one_solved': 'One Problem Solved',
        'two_solved': 'Two Problems Solved', 'three_solved': 'Three Problems Solved'
    }
    return df.rename(columns=rename_map).to_dict('records')
