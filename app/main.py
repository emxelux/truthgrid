import ast
import json
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from graph import graph_agent
from .schema import ResearchIn, ResearchOut

app = FastAPI(
    title="TruthGrid - AI Research Agent API",
    description="A Multi agent AI Research agent",
    version="0.0.1"
)
app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://truthgrid-nu.vercel.app"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"response": "The API is live and working correctly"}





@app.post("/research", response_model=ResearchOut)
async def researching(query: ResearchIn):
    response = graph_agent.invoke({"main_task": query.main_task})
    content = response.content if hasattr(response, "content") else str(response)
    draft_json = ast.literal_eval(content)
    draft = draft_json.get("draft", "")
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail = "No Draft found"
        )

    
    return {
        "draft": draft.strip()
    }