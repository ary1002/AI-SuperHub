import json
import os
import requests
from datetime import datetime, timedelta
from langchain.tools import tool


class SearchTools():

    @tool("Search the internet")
    def search_internet(query, websites=None):
        """Useful to search the internet about a given topic and return relevant results.
        Searches articles only published in the last 24 hours and can limit the search to specific websites.
        
        Args:
            query (str): The search query.
            websites (list): A list of websites to specifically search from.
        
        Returns:
            str: A string containing the top search results.
        """
        print("Searching the internet...")
        top_result_to_return = 10
        url = "https://google.serper.dev/search"

        # Get the date range for the last 24 hours
        date_from = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')

        # Create the search query with date range
        date_query = f" after:{date_from} before:{date_to}"
        
        # Add site-specific search if websites are provided
        if websites:
            site_query = " OR ".join([f"site:{site}" for site in websites])
            query = f"{query} ({site_query}) {date_query}"
        else:
            query = f"{query} {date_query}"

        payload = json.dumps({"q": query, "num": top_result_to_return, "tbm": "nws"})
        headers = {
            'X-API-KEY': os.environ['SERPER_API_KEY'],
            'content-type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        # Check if there is an organic key
        if 'organic' not in response.json():
            return "Sorry, I couldn't find anything about that, there could be an error with your Serper API key."
        else:
            results = response.json()['organic']
            string = []
            print("Results:", results[:top_result_to_return])
            for result in results[:top_result_to_return]:
                try:
                    # Attempt to extract the date
                    date = result.get('date', 'Date not available')
                    string.append('\n'.join([
                        f"Title: {result['title']}",
                        f"Link: {result['link']}",
                        f"Date: {date}",  # Include the date in the output
                        f"Snippet: {result['snippet']}",
                        "\n-----------------"
                    ]))
                except KeyError:
                    next

            return '\n'.join(string)

# Example usage
# Set your SERPER_API_KEY in the environment variables before using the tool.
# search_tool = SearchTools()
# print(search_tool.search_internet("AI advancements", ["techcrunch.com", "wired.com"]))
