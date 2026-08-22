from typing_extensions import TypedDict, Annotated, List
import operator


class ResearchState(TypedDict):
    main_task : str
    research_findings: Annotated[List[str], operator.add]
    draft: str
    critique_notes : str
    revision_number : str
    next_step:str
    current_sub_task: str
    tool_use: str