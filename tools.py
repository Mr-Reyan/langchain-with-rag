import webbrowser
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
import yt_dlp

import math
import random
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
load_dotenv()
import requests
from bs4 import BeautifulSoup
from config import GET_VIRAL_SYSTEM_PROMPT



# @tool
# def get_gaming_news(limit:int=5)->str:
#     """Get the latest gaming news from IGN."""
#     import feedparser
#     import re
#     feed_url = "https://feeds.feedburner.com/ign/games-all"
#     try:
#         feed = feedparser.parse(feed_url)

#         if not feed:
#             return "Could not fetch gaming news."

#         result = "🎮 Latest IGN Gaming News\n\n"
#         for entry in feed.entries[:limit]:
#             title = entry.get('title','No Title')
#             link = entry.get('link','#')
#             published = entry.get('published', 'Unknown Date')
#             summary = entry.get('summary', '')
#             summary = re.sub('<[^<]+?>', '', summary)[:150] + "..."
            
#             result += f"📰 {title}\n"
#             result += f"   📅 {published}\n"
#             result += f"   📝 {summary}\n"
#             result += f"   🔗 {link}\n\n"


#         return result
#     except Exception as e:
#         return f"Could not get gaming news. Error Catched:{e}"

@tool
def get_viral_gaming_news(limit: int = 10) -> str:
    """
    Get the URL of the most viral gaming news article from IGN.
    
    Args:
        limit: Number of articles to consider (default: 10)
    
    Returns:
        The URL of the most viral article
    """
    import feedparser
    import re
    
    feed_url = "https://feeds.feedburner.com/ign/games-all"
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        return "Could not fetch gaming news."
    
    articles = []
    for entry in feed.entries[:limit]:
        title = entry.get('title', 'No Title')
        summary = entry.get('summary', '')
        
        summary = re.sub('<[^<]+?>', '', summary)[:200]
        link = entry.get('link', '')
        
        articles.append({
            'title': title,
            'summary': summary,
            'link': link
        })
    
    model = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"{i}. Title: {article['title']}\n"
        articles_text += f"   Summary: {article['summary']}\n\n"
    
    system_prompt = """You are an expert editor who picks the most viral gaming news stories.
    
    Analyze these articles and pick the ONE that would go most viral on social media.
    Consider:
    - Is it surprising or shocking?
    - Does it involve a popular franchise?
    - Is there a strong emotional hook?
    - Would gamers share this?
    
    Return ONLY the number of your chosen article.
    Example: "3" """
    
    human_prompt = f"Here are the articles:\n\n{articles_text}\n\nWhich is the most viral?"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    response = model.invoke(messages)

    try:
        import re
        match = re.search(r'\d+', response.content)
        if match:
            selected_index = int(match.group()) - 1
            if 0 <= selected_index < len(articles):
                return articles[selected_index]['link']
    except:
        pass
    
    return articles[0]['link'] if articles else "No articles found"


@tool
def scrape_and_summarize_article(link:str)->str:
    """
    Scrape an article URL and generate a viral-style summary.
    
    Args:
        link: The article URL to scrape
    
    Returns:
        A viral-style summary paragraph
    """
    try:
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(link,headers=headers,timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text,'html.parser')
        article_content = soup.find('div', class_='article-content')

        text = article_content.get_text()

        text = ' '.join(text.split())
        if len(text) > 3000:
            text = text[:3000] + "..."
        title = soup.find('h1')
        title_text = title.get_text() if title else "Article"

        model = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        human_prompt = f"""Article Title: {title_text}

        Article Content:
        {text}

        Write a viral-style summary of this article."""


        messages = [
            SystemMessage(content=GET_VIRAL_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ]
        response = model.invoke(messages)
        return f"{title_text}\n\n{response.content}\n\n📰 Source: {link}"

    except Exception as e:
        return f"Error scraping article: {str(e)}"

import asyncio
from twikit import Client
@tool
def post_to_x(text: str) -> str:
    """
    Post a tweet to X.com (Twitter).
    
    Args:
        text: The content of the tweet to post.
    
    Returns:
        Success message or error string.
    """
    try:
        async def _post():
            client = Client('en-US')
            client.set_cookies({
                "auth_token": os.getenv('AUTH_TOKEN'),
                "ct0": os.getenv('CT0')
            })
            await client.create_tweet(text)
            return "Tweet posted successfully!"
        return asyncio.run(_post())
    except Exception as e:
        return f"Error: {e}"

    

@tool
def search_youtube_videos(query: str) -> str:
    """Search YouTube and open the recent video result.
        
    Args:
        query: Search term for YouTube
    """
    try:
        ydl_opts={
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'restrictfilenames': True,
            'remote_components': 'ejs:npm',
            'force_generic_extractor': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch5:{query}"
            info = ydl.extract_info(search_query,download=False)
            if info and 'entries' in info:
                videos = info['entries']

                if not videos:
                    return f"No videos found for '{query}'"

                i = 0

                while i < len(videos):
                    video = videos[i]  
                    video_duration = video.get('duration')
                    
                    if video_duration and video_duration > 180:
                        first_video = video
                        break
                    i += 1

                if not first_video:

                    first_video = videos[0]

                    
                video_url = f"https://youtube.com/watch?v={first_video['id']}"
                # video_title = first_video.get('title', 'Video')
                # upload_date = first_video.get('upload_date', 'Unknown date')

                # webbrowser.open(video_url)
                return video_url
                # return f" Opened: {video_title}\n Uploaded: {upload_date}\n {video_url}"
        
        return f" No videos found for '{query}'"
                
    except Exception as e:
        return f" Error: {str(e)}"

@tool 
def search_youtube(link:str)->str:
    """
    Open the give youtube link and watch video
    Args:
        link: YouTube video link to watch (e.g., 'https://youtube.com/watch?v=...')
    """
    webbrowser.open(link)
    return "Link opened"

@tool 
def download_youtube_video(link:str)->str:
    """
    Download YouTube video of provided link.
        
    Args:
        link: YouTube video link to download (e.g., 'https://youtube.com/watch?v=...')
    """
    try:
        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
            'remote_components': 'ejs:npm', 
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([link])
            
        if error_code == 0:
            return f"Download complete: {link}"
        else:
            return f"Download failed: {link}"
            
    except Exception as e:
        return f"Error downloading: {str(e)}"

@tool
def google_search_and_read(query: str) -> str:
    """Search Google for a query by opening Chrome browser.
    
    USE THIS TOOL WHEN:
    - The user says "search for X on Google"
    - The user says "Google X"
    - The user says "look up X on Google"
    - The user says "find X on Google"
    
    DO NOT use this for Wikipedia searches.
    
    Args:
        query: The exact search term to look up on Google
    """
    import urllib.parse

    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)
    return "searched on google"
    # headers = {"User-Agent": "Mozilla/5.0"}  # Google blocks scrapers without headers

    # response = requests.get(url, headers=headers)
    # soup = BeautifulSoup(response.text, "html.parser")

    # results = []
    # for item in soup.select(".tF2Cxc")[:5]:  # Top 5 results
    #     title = item.select_one("h3")
    #     snippet = item.select_one(".VwiC3b")
    #     if title and snippet:
    #         results.append(f"- {title.text}: {snippet.text}")

    # return "Top search results:\n" + "\n".join(results)


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
        if expression.endswith("!"):
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
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }

        safe_globals = {"__builtins__": {}, **allowed_functions}
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
            "srlimit": 1,
        }

        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()

        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return f"No Wikipedia article found for '{query}'"

        page_title = search_results[0]["title"]

        # Get the page summary
        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + page_title.replace(" ", "_")
        )
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
    google_search_and_read,
    search_youtube_videos,
    download_youtube_video,
    get_viral_gaming_news,
    scrape_and_summarize_article,
    post_to_x
    # get_gaming_news
]

# Grouped tools
UTILITY_TOOLS = [get_current_time, generate_random_number, calculate, download_youtube_video]
EXTERNAL_TOOLS = [
    get_weather,
    search_wikipedia,
    google_search_and_read,
    search_youtube_videos,
    scrape_and_summarize_article,
    get_viral_gaming_news,
    post_to_x
    # get_gaming_news,
    ]
