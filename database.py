import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# --- DATABASE CONFIG ---
# This tool uses SQLite locally and PostgreSQL in the Cloud.
# To use Cloud DB, add [connections.postgresql] to your Streamlit Secrets.

def get_connection():
    """Get a database connection based on environment (Cloud or Local)."""
    try:
        # Check if Postgres Secrets exist
        if hasattr(st, "secrets"):
            if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
                return st.connection("postgresql", type="sql")
    except:
        pass
    return None

def init_db():
    conn = get_connection()
    if conn:
        # postgresql (Cloud)
        with conn.session as session:
            session.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    ref_filename TEXT,
                    res_filename TEXT,
                    analysis_date TEXT,
                    total_students INTEGER
                )
            """)
            # Simple Migration: Add column if not exists
            try:
                session.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS analysis_date TEXT")
            except:
                pass

            session.execute("""
                CREATE TABLE IF NOT EXISTS report_data (
                    id SERIAL PRIMARY KEY,
                    report_id INTEGER,
                    branch TEXT,
                    year TEXT,
                    registered INTEGER,
                    appeared INTEGER,
                    absent INTEGER,
                    zero_solved INTEGER,
                    one_solved INTEGER,
                    two_solved INTEGER,
                    three_solved INTEGER
                )
            """)
            session.commit()
    else:
        # sqlite3 (Local)
        conn_local = sqlite3.connect("history.db")
        c = conn_local.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, ref_filename TEXT, res_filename TEXT, analysis_date TEXT, total_students INTEGER)''')
        # Simple Migration for SQLite
        try:
            c.execute("ALTER TABLE reports ADD COLUMN analysis_date TEXT")
        except:
            pass
        c.execute('''CREATE TABLE IF NOT EXISTS report_data (id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER, branch TEXT, year TEXT, registered INTEGER, appeared INTEGER, absent INTEGER, zero_solved INTEGER, one_solved INTEGER, two_solved INTEGER, three_solved INTEGER)''')
        conn_local.commit()
        conn_local.close()

def save_report(ref_filename, res_filename, analysis_date, final_df):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_row = final_df[final_df['Branch'] == 'OVERALL TOTAL']
    total_students = int(total_row.iloc[0]['No of Registered Students']) if not total_row.empty else 0

    conn = get_connection()
    if conn:
        with conn.session as s:
            # 1. Insert Metadata
            res = s.execute("INSERT INTO reports (timestamp, ref_filename, res_filename, analysis_date, total_students) VALUES (:t, :ref, :res, :ad, :tot) RETURNING id", 
                         {"t": timestamp, "ref": ref_filename, "res": res_filename, "ad": analysis_date, "tot": total_students})
            report_id = res.fetchone()[0]
            
            # 2. Insert Data
            for _, row in final_df.iterrows():
                s.execute("""INSERT INTO report_data (report_id, branch, year, registered, appeared, absent, zero_solved, one_solved, two_solved, three_solved) 
                           VALUES (:rid, :b, :y, :r, :a, :ab, :z, :o, :t, :th)""",
                         {"rid": report_id, "b": row['Branch'], "y": row['Year'], "r": int(row['No of Registered Students']), 
                          "a": int(row['No of Students Appeared']), "ab": int(row['No of Students Absent']), 
                          "z": int(row['Zero Problems Solved']), "o": int(row['One Problem Solved']), 
                          "t": int(row['Two Problems Solved']), "th": int(row['Three Problems Solved'])})
            s.commit()
            return report_id
    else:
        conn_local = sqlite3.connect("history.db")
        c = conn_local.cursor()
        c.execute("INSERT INTO reports (timestamp, ref_filename, res_filename, analysis_date, total_students) VALUES (?, ?, ?, ?, ?)", (timestamp, ref_filename, res_filename, analysis_date, total_students))
        report_id = c.lastrowid
        for _, row in final_df.iterrows():
            c.execute("INSERT INTO report_data (report_id, branch, year, registered, appeared, absent, zero_solved, one_solved, two_solved, three_solved) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (report_id, row['Branch'], row['Year'], int(row['No of Registered Students']), int(row['No of Students Appeared']), int(row['No of Students Absent']), int(row['Zero Problems Solved']), int(row['One Problem Solved']), int(row['Two Problems Solved']), int(row['Three Problems Solved'])))
        conn_local.commit()
        conn_local.close()
        return report_id

def get_all_reports():
    conn = get_connection()
    if conn:
        return conn.query("SELECT * FROM reports ORDER BY id DESC")
    
    conn_local = sqlite3.connect("history.db")
    df = pd.read_sql_query("SELECT * FROM reports ORDER BY id DESC", conn_local)
    conn_local.close()
    return df

def get_report_data(report_id):
    conn = get_connection()
    if conn:
        df = conn.query("SELECT * FROM report_data WHERE report_id = :rid", params={"rid": report_id})
    else:
        conn_local = sqlite3.connect("history.db")
        df = pd.read_sql_query("SELECT * FROM report_data WHERE report_id = ?", conn_local, params=(report_id,))
        conn_local.close()
    
    if df.empty: return df
    
    df = df.drop(columns=['id', 'report_id'])
    rename_map = {
        'branch': 'Branch', 'year': 'Year', 'registered': 'No of Registered Students',
        'appeared': 'No of Students Appeared', 'absent': 'No of Students Absent',
        'zero_solved': 'Zero Problems Solved', 'one_solved': 'One Problem Solved',
        'two_solved': 'Two Problems Solved', 'three_solved': 'Three Problems Solved'
    }
    return df.rename(columns=rename_map)

