import uvicorn
import os

if __name__ == "__main__":
    # Ensure history.db is initialized
    from database import init_db
    init_db()
    
    print("🚀 Starting Skill Rack Analysis Backend...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
