from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_conversation
from app.core.config import settings
from app.core.database import create_tables

app = FastAPI(
    title="Team Activity Monitor API",
    description="API for monitoring team activity across JIRA and GitHub",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Include routers
app.include_router(routes_conversation.router, tags=["conversations"])

@app.get("/")
def read_root():
    return {"message": "Team Activity Monitor API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
