
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from serpapi import Client
import os
from dotenv import load_dotenv
load_dotenv()


class QAState(TypedDict):
    question:str
    search_results:list[str]
    attempts: int
    max_attempts: int
    answer: str

def search_google(query: str) -> list[str]:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("⚠️  WARNING: No SERPAPI_KEY found. Using mock data.")
        return [f"Mock result for: {query}", f"Another mock result for: {query}"]
    client = Client(api_key=api_key)

    params={
        'q':query,
        'engine':'google',
        'num':3
    }
    search = client.search(params)

    snippets = []
    for result in search.get("organic_results", [])[:3]:
        snippet = result.get("snippet", "")
        if snippet:
            snippets.append(snippet)
    
    return snippets


def search_node(state: QAState) -> QAState:
    """ search for information """
    if state['attempts'] == 0:
        query = state['question']
    elif state['attempts'] == 1:
        query = f"{state['question']} information"
    else:
        query = f"{state['question']} details"

    print(f"\n🔍 Searching... {query}")
    results = search_google(query)
    state['search_results'] = results
    state['attempts'] +=1 
    print(f"Found {len(results)} results")
    return state

def check_node(state: QAState) -> QAState:
    """Check if we have enough info"""
    print("\nChecking results...")

    has_info = len(state['search_results']) > 0
    if not has_info and state['attempts'] <state['max_attempts']:
        state['answer'] = ""
    else:
        if has_info:
            state['answer'] = f"Based on search results:\n" + "\n".join(state['search_results'])
        else:
            state['answer'] = f"Sorry, couldn't find information about '{state['question']}'"

    return state

def answer_node(state: QAState) -> QAState:
    """Final answer"""

    if state['search_results']:
        answer = f"📌 Answer: {state['question']}\n\n"
        answer += "Key points:\n"
        for i, result in enumerate(state['search_results'], 1):
            answer += f"{i}. {result}\n"
        state['answer'] = answer
    else:
        state['answer'] = f"❌ No information found for: {state['question']}"
    
    return state

def should_continue(state: QAState) -> Literal['search','answer']:
    """Decide if we should search again"""

    if state['answer']:
        print("✅Answer ready, stopping")
        return "answer"

    if state['attempts']>=state['max_attempts']:
        print("⏹️Max attempts reached, stopping")
        return "answer"
    print("🔄 Need more info, searching again")
    return "search"

def create_qa_bot():
    """Create the QA bot"""
    graph = StateGraph(QAState)

    graph.add_node('search',search_node)
    graph.add_node('check',check_node)
    graph.add_node('answer',answer_node)

    graph.set_entry_point('search')

    graph.add_edge('search','check')

    graph.add_conditional_edges(
        'check',
        should_continue,
        {
            "search": "search",   
            "answer": "answer"    
        }
    )
    graph.add_edge('answer',END)

    return graph.compile()


def ask_question(question: str):
    """Ask a question"""
    print("=" * 50)
    print(f"❓ Question: {question}")
    print("=" * 50)

    state = QAState(
        question=question,
        search_results=[],
        answer="",
        attempts=0,
        max_attempts=3,
    )

    app = create_qa_bot()
    final_state=app.invoke(state)
    print("\n" + "=" * 50)
    print("📝 FINAL ANSWER")
    print("=" * 50)
    print(final_state['answer'])
    print("-" * 50)
    print(f"Attempts: {final_state['attempts']}")
    print(f"Results found: {len(final_state['search_results'])}")
    print("=" * 50)
    
    return final_state

if __name__ == '__main__':
    questions = [
        "What is the capital of Australia?",
        "What is quantum computing?",
        "What are the benefits of exercise?",
        "Who is the CEO of Tesla?",
        "What is the population of Tokyo?"
    ]

    for q in questions:
        ask_question(q)
        print("\n" + "-" * 50 + "\n")
