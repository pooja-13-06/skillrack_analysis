from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd
import io
import json
from fastapi.responses import StreamingResponse
import processor, database, exporter

app = FastAPI(title="Skill Rack Analysis API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Especific origin for React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    database.init_db()

# Store current report data in memory for download (simplification for this phase)
# In a real app, this should be in a cache or temporary storage
# Store current data in memory for download
CURRENT_REPORTS = []
CURRENT_WEEKLY = []
CURRENT_PERFORMANCE = []
PERF_INFO = {"branch": "OVERALL", "top_n": 50}

@app.post("/process")
async def process_files(files: List[UploadFile] = File(...)):
    global CURRENT_REPORTS
    # ... existing processing code ... (preserving logic)
    all_dfs = []
    for file in files:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith('.csv') else pd.read_excel(io.BytesIO(contents))
        df = processor.standardize_columns(df)
        df['Source_Filename'] = file.filename
        all_dfs.append(df)
    
    if not all_dfs: raise HTTPException(status_code=400, detail="No valid files uploaded")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    CURRENT_REPORTS = processor.generate_daily_reports(combined_df)
    for rep in CURRENT_REPORTS:
        database.save_report("Upload", "Multiple", rep['date'], pd.DataFrame(rep['data']))
    return CURRENT_REPORTS

@app.get("/download/daily")
async def download_daily():
    if not CURRENT_REPORTS: raise HTTPException(status_code=400, detail="No daily reports available")
    excel_data = exporter.generate_excel_report(CURRENT_REPORTS)
    return StreamingResponse(io.BytesIO(excel_data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Skill_Rack_Daily_Analysis.xlsx"})

@app.post("/weekly")
async def process_weekly(files: List[UploadFile] = File(...)):
    global CURRENT_WEEKLY
    # ... existing processing code ...
    all_dfs = []
    for file in files:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith('.csv') else pd.read_excel(io.BytesIO(contents))
        df = processor.standardize_columns(df)
        all_dfs.append(df)
    
    if not all_dfs: raise HTTPException(status_code=400, detail="No valid files uploaded")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    CURRENT_WEEKLY = processor.generate_weekly_report(combined_df)
    return CURRENT_WEEKLY

@app.get("/download/weekly")
async def download_weekly():
    if not CURRENT_WEEKLY: raise HTTPException(status_code=400, detail="No weekly report available")
    excel_data = exporter.generate_weekly_excel(CURRENT_WEEKLY)
    return StreamingResponse(io.BytesIO(excel_data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Skill_Rack_Weekly_Leaderboard.xlsx"})

@app.post("/performance")
async def process_performance(files: List[UploadFile] = File(...), top_n: int = Form(50), branch: str = Form("OVERALL")):
    global CURRENT_PERFORMANCE, PERF_INFO
    PERF_INFO = {"branch": branch, "top_n": top_n}
    # ... same as before but now with global storage ...
    all_dfs = []
    for file in files:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith('.csv') else pd.read_excel(io.BytesIO(contents))
        df = processor.standardize_columns(df)
        all_dfs.append(df)
    if not all_dfs: raise HTTPException(status_code=400, detail="No valid files uploaded")
    try:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        if branch != "OVERALL":
            combined_df['Branch'] = combined_df['Branch'].apply(processor.normalize_branch)
            combined_df = combined_df[combined_df['Branch'] == branch]
        if combined_df.empty: return []
        aggregated_data = processor.generate_weekly_report(combined_df) 
        CURRENT_PERFORMANCE = processor.get_top_performers(pd.DataFrame(aggregated_data), top_n)
        return CURRENT_PERFORMANCE
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/download/performance")
async def download_performance():
    if not CURRENT_PERFORMANCE: raise HTTPException(status_code=400, detail="No performance analysis available")
    excel_data = exporter.generate_performance_excel(CURRENT_PERFORMANCE, PERF_INFO['branch'], PERF_INFO['top_n'])
    return StreamingResponse(io.BytesIO(excel_data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=Skill_Rack_Top_Performers_{PERF_INFO['branch']}.xlsx"})

@app.get("/download")
async def download_legacy():
    # Keep as fallback for daily
    return await download_daily()

@app.get("/history")
def get_history():
    return database.get_all_reports()

@app.get("/history/{report_id}")
def get_report_detail(report_id: int):
    return database.get_report_data(report_id)
