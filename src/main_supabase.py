from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.routes import note_supabase, user_supabase

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Serve SPA index at root for convenience when running FastAPI locally
@app.get("/")
async def root_index():
    return FileResponse("src/static/index.html")

# Include routers under /api to match frontend fetch URLs
app.include_router(note_supabase.router, prefix="/api")
app.include_router(user_supabase.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)