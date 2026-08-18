
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from serpapi import Client
import os
from dotenv import load_dotenv
load_dotenv()

class ResearchState(TypedDict):
    topic:str

    research_questions: list[str]

    search_queries: list[str]

    sources: list[dict]

    summaries: list[dict]

    research_notes: str

    iteration: int

    max_iterations: int

    research_complete: bool

    final_report: str

    pdf_path: str


def planner_node(state:ResearchState)->ResearchState:
    pass

def search_node(state:ResearchState)->ResearchState:
    pass

def read_sources_node(state:ResearchState)->ResearchState:
    pass

def extract_node(state:ResearchState)->ResearchState:
    pass

def check_research_node(state:ResearchState)->ResearchState:
    pass

def synthesize_node(state:ResearchState)->ResearchState:
    pass

def critic_node(state:ResearchState)->ResearchState:
    pass

def pdf_generator_node(state:ResearchState)->ResearchState:
    pass