# tools.py
from langchain.tools import tool
import requests
import math
import random
from datetime import datetime

# ---------- BASIC TOOLS ----------

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def generate_random_number(start: int, end: int) -> str:
    """Generate a random number between start and end.
    
    Args:
        start: The lower bound (inclusive)
        end: The upper bound (inclusive)
    """
    try:
        result = random.randint(start, end)
        return f"Random number between {start} and {end}: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression. Supports factorial with '!'.
    
    Args:
        expression: A mathematical expression like '10!', '2+2', 'sqrt(16)'
    """
    try:
        expression = expression.strip()
        
        # Handle factorial (e.g., "10!")
        if expression.endswith('!'):
            try:
                num = int(expression[:-1])
                if num < 0:
                    return "Error: Factorial of negative number is undefined"
                result = math.factorial(num)
                return f"Result: {result}"
            except ValueError:
                return "Error: Invalid factorial expression"
        
        # Safe eval with allowed math functions
        allowed_functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }
        
        safe_globals = {'__builtins__': {}, **allowed_functions}
        result = eval(expression, safe_globals, {})
        
        if isinstance(result, float):
            if result.is_integer():
                return f"Result: {int(result)}"
            return f"Result: {result:.6f}"
        return f"Result: {result}"
    
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_weather(city: str) -> str:
    """Get weather for a city.
    
    Args:
        city: City name (e.g., 'London', 'New York')
    """
    try:
        response = requests.get(f"https://wttr.in/{city}?format=%C+%t")
        if response.status_code == 200:
            return f"Weather in {city}: {response.text.strip()}"
        return f"Could not fetch weather for {city}"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information about a topic.
    
    Args:
        query: The topic to search for (e.g., 'Albert Einstein', 'Eiffel Tower')
    """
    try:
        # Search for the page
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1
        }
        
        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return f"No Wikipedia article found for '{query}'"
        
        page_title = search_results[0]["title"]
        
        # Get the page summary
        summary_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + page_title.replace(" ", "_")
        summary_response = requests.get(summary_url, timeout=10)
        summary_response.raise_for_status()
        summary_data = summary_response.json()
        
        extract = summary_data.get("extract", "No summary available")
        page_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
        
        # Truncate if too long
        if len(extract) > 1000:
            extract = extract[:1000] + "..."
        
        return f"**{page_title}**\n\n{extract}\n\nRead more: {page_url}"
    
    except requests.exceptions.Timeout:
        return f"Timeout while searching for '{query}'. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# ---------- EXPORTS ----------
ALL_TOOLS = [
    get_current_time,
    generate_random_number,
    calculate,
    get_weather,
    search_wikipedia,
]

# Grouped tools
UTILITY_TOOLS = [get_current_time, generate_random_number, calculate]
EXTERNAL_TOOLS = [get_weather, search_wikipedia]