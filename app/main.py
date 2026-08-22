import json
from fastapi import FastAPI, HTTPException, status
from graph import graph_agent
from .schema import ResearchIn, ResearchOut

app = FastAPI(
    title="TruthGrid - AI Research Agent API",
    description="A Multi agent AI Research agent",
    version="0.0.1"
)


@app.get("/")
def health_check():
    return {"response": "The API is live and working correctly"}



@app.post("/research", response_model=ResearchOut)
async def researching(query: ResearchIn):
    response = graph_agent.invoke({"main_task": query.main_task})
    content = response.content if hasattr(response, "content") else str(response)
    draft = content.split("draft")[1]
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail = "No Draft found"
        )

    return {
        "draft": draft
    }