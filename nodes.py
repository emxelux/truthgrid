from agents import logging
from state import ResearchState
from agents import (
    create_critique_chain,
    create_researcher_chain,
    create_supervisor_chain,
    create_writer_chain
)

supervisor_agent = create_supervisor_chain()
researcher_agent = create_researcher_chain()
critiquer_agent = create_critique_chain()
writer_agent = create_writer_chain()




def supervisor_node(state: ResearchState) -> dict:
    """Supervisor decides the next step"""
    logging.info("===============SUPERVISOR AGENT========================")
    decision = supervisor_agent(state)

    next_step = decision.get("next_step", "researcher")
    task_desc = decision.get("task_description", "Continue work")

    logging.info(f"Next step: {next_step}")
    logging.info(f"Task Desc: {task_desc}")

    return {
        "next_step": next_step,
        "current_sub_task": task_desc
    }


def researcher_node(state: ResearchState) -> dict:
    """Research node that gather information"""
    logging.info("================Researcher===================")

    sub_task = state.get("current_sub_task", state.get("main_task"))
    logging.info(F"RESEARCHING: {sub_task}")
    try:
        result = researcher_agent({"input": sub_task})
        findings = (result or {}).get("output", "Research Completed ✔️")
        logging.info(f"Findings: \n\n=============================\n{findings}\n\n======")

    except Exception as e:
        logging.error(f"Research error: {e}")
        findings = f"Research on {sub_task} gathered"
    return {
        "research_findings": [findings]
    }


def writer_node(state: ResearchState) -> dict:
    """Writer Node that create draft"""
    logging.info("=============WRITER NODE===========")
    draft = writer_agent(state)
    logging.info(f"Draft Created: {draft}")
    return {
        "draft": draft,
        "revision_number": str(int(state.get("revision_number", 0)) + 1)
    }



def critique_node(state: ResearchState):
    """Critique node that reviews the draft"""
    logging.info(f"========================= CRITIQUER NODE =====================")
    critiques = critiquer_agent(state)
    is_approved = "APPROVED" in str(critiques).upper()

    if is_approved:
        logging.info("Draft approved")
        return {
            "critique_notes": "APPROVED",
            "next_step": "END"
        }
    else:
        logging.info("Needs Reviewing again")
        return {
            "critique_notes": str(critiques),
            "next_step": "researcher"
        }



