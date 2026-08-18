
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from serpapi import Client
import os
from dotenv import load_dotenv
load_dotenv()

class ResearchState(TypedDict):
    pass