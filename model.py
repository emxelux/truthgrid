import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",                              
    filemode="w"
)


def _call_llm(llm_obj , *args, **kwargs):
    if hasattr(llm_obj, "invoke"):
        return llm_obj.invoke(*args, **kwargs)
    if hasattr(llm_obj, "run"):
        return llm_obj.run(*args, **kwargs)
    raise AttributeError("LLM Object has no invoke/Run Object")
