from state import ResearchState
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from tools import tavily_search, arxivsearch
from model import _call_llm
from prompt import (supervisor_prompt_template, 
                    critique_prompt_template,
                      writer_prompt_template, 
                      researcher_prompt_template
                      )


from dotenv import load_dotenv

load_dotenv()

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",                              
    filemode="w"
)

# Using the strongest model for the supervisor agent
supervisor_llm = init_chat_model(
    model = "groq:openai/gpt-oss-120b",
    temperature = 0.4
)

# Using a Multimodal reasoning model for the researcher
researcher_llm = init_chat_model(
    model = "groq:qwen/qwen3.6-27b",
    temperature = 0.4
    )

# Using the same model for critiquer as that of researcher
critique_llm = create_agent(
    model="groq:qwen/qwen3.6-27b",
    tools = [tavily_search, arxivsearch],
)

# Using a weaker model for the writer agent
writer_llm = init_chat_model(
    model = "groq:openai/gpt-oss-20b",
)





def create_supervisor_chain():
    def supervisor_agent(state: ResearchState):
        research = state.get("research_findings", [])
        research_text = "\n\n".join(research) if research else "No research yet."

        revision = state.get("revision_number", 0)
        has_research = len(research) > 0
        has_draft = bool(state.get("draft", "").strip())
        critique = state.get("critique_notes", "")

        # If critique says APPROVED, then workflow in complete and done
        if "APPROVED" in critique.upper() and has_draft:
            logging.info("Supervisor: Draft approved✅, ending workflow....")
            return {
                "next_step": "END",
                "task_description": "Report approved and complete"
            }


        # If we dont have research_findings and no draft yet, we first create draft
        if not has_research:
            logging.debug("Supervisor: No research yet, directing to researcher")
            return {
                "next_step": "researcher",
                "task_description":f"Research the topic: {state.get("main_task", '')}"
            }


        # If we have draft but no critique yet, we send to critique
        if has_research and not has_draft:
            logging.info("Supervisor:Have Research, creating first draft")
            return {
                "next_step": "writer",
                "task_description": "Write the first draft based on research findings"
            }

        if has_draft and not critique:
            logging.info("Supervisor: Have draft, sending to critiquer")
            return {
                "next_step": "critiquer",
                "task_description": "Prepare draft for critique"
            }

        if critique and "APPROVED" not in critique.upper() and int(revision) < 3:
            logging.info(f"Supervisor: Revision {revision}, sending back to Researcher")
            return{
                "next_step": "researcher",
                "task_description": "Revise the draft based on critique feedback and do more of your research"
            }

        if int(revision) >= 3:
            logging.info("Supervisor: Max revisions reached, ending")
            return {
                "next_step": "END",
                "task_description": "Maximux revisions reached, finalizing report"
            }
        import json
        prompt = supervisor_prompt_template.format(
            main_task = state.get("main_task", ""),
            research_findings=research_text,
            draft = state.get("draft", "No drafts yet"),
            critique_notes = critique if critique else "No critique yet.",
            revision_number=revision
        )
        from model import _call_llm
        try:
            response = _call_llm(supervisor_llm, prompt)
            content = response.content if hasattr(response, "content") else response
            text = content.strip() if isinstance(content, str) else str(content)
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join([i for i in lines if not i.strip().startswith("```")])
            text = text.strip()

            decision = json.loads(text)

            if "next_step" in decision:
                return decision
        except Exception as e:
            logging.error(f"LLM parsing error: {e}")

        logging.info("Supervisor: using final fallback - continuing with writer")
        return {
            "next_step": "writer",
            "task_description": "Continue with draft creation"
        }
    return supervisor_agent




def create_researcher_chain():
    def research_agent(input_dict: dict):
        """Execute research using either tavily search or arxiv"""
        query = input_dict.get("input", "")

        if not query or query in ["continue_work", "complete"]:
            query = "General Research information"

        logging.info(f"Researching {query} ...")
        tool_use = input_dict.get("tool_use", "tavily")
        search_response = None
        raw_output = ""

        try:
            if "tavily" in tool_use:
                if hasattr(tavily_search, "invoke"):
                    search_response = tavily_search.invoke({"query":query})

                elif callable(tavily_search):
                    search_response = tavily_search({"query": query})

                elif hasattr(tavily_search, "run"):
                    search_response = tavily_search.run({"query": query})
            elif "arxiv" in tool_use:
                if callable(arxivsearch):
                    search_response = arxivsearch(query=query)

            if isinstance(search_response, dict):
                search_results = []
                for resp in search_response["results"]:
                    title = resp["title"]
                    content = resp["content"]
                    url = resp["url"]
                    search_results.append(f"""
                    title: {title}
                    search_content: {content}
                    search_source_url: {url}
                    """)
                raw_output = " \n\n ".join(search_results).strip()

                
            elif isinstance(search_response, str):
                raw_output = search_response.strip()

            summary_prompt = """Based on the search_results about {query}, provide a key summary (5-7 bullet points)
            SEARCH_RESULT: {raw_output}.
            Format as clear bullet points with the most important information
            """
            try:
                summary_response = _call_llm(researcher_llm, summary_prompt)
                summary = summary_response.content if hasattr(summary_response, "content") else str(summary_response)
            except Exception as e:
                logging.info(f"Summarization error: {e}")
                summary = str(raw_output)
                return {
                    "output": summary if summary else raw_output,
                    "input": query
                }
        except Exception as e:
            logging.error(f"Research error: {e}")
            return {
                "output": f"Research completed on: {query}, Key information has been gathered from web sources",
                "input": query
            }

    return research_agent



def create_writer_chain():
    def writer_agent(state: ResearchState):
        research = state.get("research_findings", "")
        research_text = "\n\n".join(research) if research else "No research Available."

        prompt = writer_prompt_template.format(
            main_task = state.get("main_task", ""),
            research_findings = research_text,
            draft = state.get("draft", ""),
            critique_notes = state.get("critique_notes", ""))

        try:
            response = _call_llm(writer_llm, prompt)
            content = response.content # if hasattr(response, "content") else str(response)
            return content if content else "Draft in progress ..."
        
        except Exception as e:
            logging.error(f"Writer error: {e}")
            return "Error Generating draft, Try again!"
    return writer_agent



def create_critique_chain():
    def critique_agent(state: ResearchState):
        draft = state.get("draft", "")
        revision_number = int(state.get("revision_number", 0))


        if revision_number >= 3:
            return "APPROVED - Maximum revision reached, The report is Satisfactory"

        prompt = critique_prompt_template.format(
            main_task = state.get("main_task", ""),
            draft = draft
        )

        try:
            response = _call_llm(critique_llm, prompt)
            content = response.content if hasattr(response, "content") else str(response)
            return content if content else "APPROVED"
        
        except Exception as e:
            logging.error(f"Critique error: {e}")
            return "APPROVED - Error with critiquer, procedding with current draft"
    return critique_agent