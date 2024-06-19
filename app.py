from flask import Flask, render_template, request, redirect, url_for
from crewai import Crew, Process
from agents import AINewsLetterAgents
from tasks import AINewsLetterTasks
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from datetime import datetime
import asyncio
from flask_caching import Cache
import markdown

load_dotenv()

app = Flask(__name__)

# Configure Flask-Caching
app.config['CACHE_TYPE'] = 'simple'  # You can use 'redis' or 'memcached' for more robust solutions
app.config['CACHE_DEFAULT_TIMEOUT'] = 43200  # 12 hours in seconds
cache = Cache(app)

# Function to save task output as markdown
async def save_markdown(task_output):
    # Get today's date in the format YYYY-MM-DD
    today_date = datetime.now().strftime('%Y-%m-%d')
    # Set the filename with today's date
    filename = f"{today_date}.md"
    # Write the task output to the markdown file
    with open(filename, 'w') as file:
        file.write(task_output)
    print(f"Newsletter saved as {filename}")

# Initialize the agents and tasks
tasks = AINewsLetterTasks()
llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                           verbose=True,
                           temperature=0.5,
                           google_api_key=os.getenv("GOOGLE_API_KEY_B"))
agents = AINewsLetterAgents()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_newsletter', methods=['POST'])
def generate_newsletter():
    # Check if we have a cached newsletter
    cached_newsletter = cache.get('newsletter')
    if cached_newsletter:
        return redirect(url_for('view_newsletter'))

    # Create a new event loop to run the asynchronous operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_and_cache_newsletter())
    return redirect(url_for('view_newsletter'))

async def run_crew_and_save_markdown():
    # Instantiate the agents
    editor = agents.editor_agent()
    news_fetcher = agents.news_fetcher_agent()
    news_analyzer = agents.news_analyzer_agent()
    newsletter_compiler = agents.newsletter_compiler_agent()

    # Instantiate the tasks
    fetch_news_task = tasks.fetch_news_task(news_fetcher)
    analyze_news_task = tasks.analyze_news_task(news_analyzer, [fetch_news_task])
    compile_newsletter_task = tasks.compile_newsletter_task(
        newsletter_compiler, [analyze_news_task], save_markdown)

    # Form the crew
    crew = Crew(
        agents=[editor, news_fetcher, news_analyzer, newsletter_compiler],
        tasks=[fetch_news_task, analyze_news_task, compile_newsletter_task],
        process=Process.hierarchical,
        manager_llm=llm,
        verbose=2
    )

    # Kick off the crew's work
    results = crew.kickoff()

    # Save results to a markdown file
    await save_markdown(results)
    return results

async def run_and_cache_newsletter():
    results = await run_crew_and_save_markdown()
    cache.set('newsletter', results)

@app.route('/newsletter')
def view_newsletter():
    # Check if we have a cached newsletter
    newsletter_content = cache.get('newsletter')
    if not newsletter_content:
        return redirect(url_for('index'))

    # Assuming the markdown file is saved with the current date
    today_date = datetime.now().strftime('%Y-%m-%d')
    filename = f"{today_date}.md"

    with open(filename, 'r') as file:
        newsletter_content = file.read()
    html_content=markdown.markdown(newsletter_content)

    return render_template('newsletter.html', content=html_content)

if __name__ == '__main__':
    app.run(debug=True)
