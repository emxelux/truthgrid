from graph import graph_agent
# from fastapi import FastAPI
from schema import ResearchIn
from typing import Any, cast

# app = FastAPI()


# @app.post("/")
# def research(query: ResearchIn):
#     response = graph_agent.invoke(query)
#     return {
#         "research_result"
#     }


research_response = graph_agent.invoke(
	cast(Any, {"main_task": "What are the latest Development in AI"})
)
draft = research_response if hasattr(research_response, "content") else str(research_response)
print(draft)