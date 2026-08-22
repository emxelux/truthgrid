from langgraph.graph import StateGraph, START, END
from state import ResearchState
from nodes import (
    supervisor_node,
    writer_node,
    researcher_node,
    critique_node
)



def build_graph():
    workflow = StateGraph(ResearchState)
    
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("critiquer", critique_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("writer", "critiquer")
    workflow.add_edge("critiquer", "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_step", "researcher"),
        {
            "researcher": "researcher",
            "writer": "writer",
            "critiquer":"critiquer",
            "END": END
        }
    )
    app = workflow.compile()
    return app

graph_agent = build_graph()
with open("graph_diagram.mmd", "w", encoding="utf-8") as f:
    f.write(graph_agent.get_graph().draw_mermaid())