from pydantic import BaseModel


class ResearchIn(BaseModel):
    main_task : str


class ResearchOut(BaseModel):
    draft: str