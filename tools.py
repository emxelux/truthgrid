from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_community.tools import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper
from langchain.tools import tool
import arxiv


load_dotenv()



tavily_search = TavilySearch(max_results=3)


def arxivsearch(query:str ):
   """Use Arxiv search to run a research query using the 'query' parameter"""
   searcher =  ArxivAPIWrapper(
      arxiv_search=arxiv,
      arxiv_exceptions=(ConnectionError),
        top_k_results=3,
        doc_content_chars_max=2000,
    )
   response = searcher.run(query)
   return response