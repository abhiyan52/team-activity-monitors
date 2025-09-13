from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_jira, routes_github, routes_activity
from app.core.config import settings

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

# Include routers
app.include_router(routes_jira.router, prefix="/api/jira", tags=["jira"])
app.include_router(routes_github.router, prefix="/api/github", tags=["github"])
app.include_router(routes_activity.router, prefix="/api/activity", tags=["activity"])

@app.get("/")
def read_root():
    return {"message": "Team Activity Monitor API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
