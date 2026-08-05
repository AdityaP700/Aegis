import os
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from tools.base import BaseTool
from engine.types import ExecutionRequest

load_dotenv()

class SearchTool(BaseTool):
    """
    Searches the web using SerpAPI.

    The executor doesn't know if this is Google, Bing, or DuckDuckGo.
    It just sends a query and gets results.
    """

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError(
                "SERPAPI_KEY not found in .env file. "
                "Get a free key at https://serpapi.com (100 searches/month)"
            )
        self.base_url = "https://serpapi.com/search"

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Searches the web and returns top results with titles, URLs, and snippets"

    def _fetch_from_api(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Fetch search results from SerpAPI.

        Args:
            query: Search query string
            num_results: Number of results to return (default 5)

        Returns:
            Raw JSON from SerpAPI

        Raises:
            ConnectionError: API issues or rate limits
            ValueError: Invalid API key
        """
        self.engine = os.getenv("SEARCH_ENGINE", "google")
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": self.engine,      # Could be "bing", "duckduckgo" — executor doesn't know!
            "num": num_results
        }

        response = requests.get(self.base_url, params=params, timeout=15)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise ValueError("Invalid SERPAPI_KEY. Check your .env file.")
        elif response.status_code == 429:
            raise ConnectionError("Search API rate limit exceeded. Try again later.")
        elif response.status_code == 503:
            raise ConnectionError("Search service unavailable. Try again later.")
        else:
            raise ConnectionError(
                f"Search API returned status {response.status_code}: {response.text}"
            )

    def _normalize_response(self, raw_data: Dict[str, Any], query: str,num_results: int = 5) -> List[Dict[str, str]]:
        """
        Extract and normalize search results.

        SerpAPI returns a LOT of data (organic results, ads, knowledge graph, etc.)
        We only extract the organic results.

        Args:
            raw_data: Raw JSON from SerpAPI
            query: Original search query

        Returns:
            List of normalized search results
        """
        organic_results = raw_data.get("organic_results", [])
        organic_results = organic_results[:num_results]
        normalized = []
        for result in organic_results:
            normalized.append({
                "title": result.get("title"),
                "url": result.get("link"),
                "snippet": result.get("snippet"),
                "position": result.get("position"),
                "source": result.get("source")
            })

        return normalized

    def execute(self, request: ExecutionRequest, trace: list) -> Dict[str, Any]:
        """
        Execute web search through Aegis.

        Args:
            request: ExecutionRequest with query in arguments
            trace: Trace list for observability

        Returns:
            Dict with search results and metadata
        """
        query = request.arguments.get("query")
        if not query:
            raise ValueError("'query' argument is required")

        num_results = request.arguments.get("num_results", 5)

        # Trace: Starting search
        trace.append({
            "component": "search_tool",
            "event": "search_started",
            "query": query,
            "num_results": num_results
        })

        try:
            # Fetch from search API
            raw_data = self._fetch_from_api(query, num_results)

            # Trace: API responded
            total_results = raw_data.get("search_information", {}).get("total_results", 0)
            trace.append({
                "component": "search_tool",
                "event": "api_response_received",
                "query": query,
                "total_results_available": total_results
            })

            # Normalize results
            normalized = self._normalize_response(raw_data, query,num_results)

            # Trace: Normalization done
            trace.append({
                "component": "search_tool",
                "event": "results_normalized",
                "query": query,
                "results_returned": len(normalized)
            })

            return {
                "query": query,
                "results": normalized,
                "total_results": len(normalized)
            }

        except ValueError as e:
            # Bad API key — fatal
            trace.append({
                "component": "search_tool",
                "event": "api_error_fatal",
                "query": query,
                "error": str(e)
            })
            raise

        except Exception as e:
            # Network errors, rate limits — retryable
            trace.append({
                "component": "search_tool",
                "event": "api_error_operational",
                "query": query,
                "error": str(e)
            })
            raise