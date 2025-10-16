import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.routes import note_supabase
from src.db_config import supabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="NoteTaker")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(note_supabase.router, prefix="/api")

# Create static directory if it doesn't exist
static_folder = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(static_folder, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_folder), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the Single Page Application"""
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    file_path = os.path.join(static_folder, full_path)
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        index_path = os.path.join(static_folder, 'index.html')
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="File not found")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
