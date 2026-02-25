# Skill Rack Analysis Tool - Modern Version

This is a modernized version of the Skill Rack Analysis tool, built with a **React (Vite)** frontend and a **FastAPI** backend.

## Prerequisites
- Node.js (v18 or higher)
- Python (3.9 or higher)

## Setup & Running

### 1. Backend (FastAPI)
The backend handles all data processing, Excel generation, and history tracking.
```bash
cd backend
pip install -r requirements.txt
python run.py
```
*Backend will be running at: `http://localhost:8000`*

### 2. Frontend (React + Vite)
The frontend provides a premium, responsive web interface.
```bash
cd frontend
npm install
npm run dev
```
*Frontend will be running at: `http://localhost:5173`*

## Login
- **Password**: `cit` (Same as the original tool)

## Features
- **Modern UI**: Swiss-inspired design with dark/light mode support.
- **Daily Analysis**: Upload multiple files to generate daily attendance and performance reports.
- **Weekly Analysis**: Automated leaderboard based on weekly problem-solving trends.
- **Excel Export**: Download professional Excel reports directly from the web interface.
- **History Tracking**: Access past report data instantly.
