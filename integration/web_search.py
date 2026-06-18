"""
prompt-orchestrator — Web Search
Privacy-respecting web search integration
"""

import os
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime

class WebSearch:
    """
    Web search with privacy respect.
    Supports multiple backends: SearXNG, DuckDuckGo, etc.
    """
    
    def __init__(self, searxng_url: str = None):
        self.searxng_url = searxng_url or os.environ.get('SEARXNG_URL', 'http://localhost:8888')
        self.use_searxng = searxng_url is not None
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search the web"""
        
        if self.use_searxng:
            return self._search_searxng(query, num_results)
        else:
            return self._search_duckduckgo(query, num_results)
    
    def _search_searxng(self, query: str, num_results: int) -> List[Dict]:
        """Search using SearXNG instance"""
        
        try:
            response = requests.get(
                f"{self.searxng_url}/search",
                params={
                    'q': query,
                    'format': 'json',
                    'engines': 'google,duckduckgo,bing',
                    'num_results': num_results
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('results', []):
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'content': item.get('content', '')[:300],
                        'engine': item.get('engine', '')
                    })
                
                return results
            
        except Exception as e:
            print(f"SearXNG search error: {e}")
        
        return self._search_duckduckgo(query, num_results)
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo (fallback)"""
        
        try:
            # Using ddg API via html
            url = "https://html.duckduckgo.com/html/"
            response = requests.post(
                url,
                data={'q': query, 'b': ''},
                timeout=30
            )
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                results = []
                for result in soup.select('.result'):
                    title_elem = result.select_one('.result__title')
                    link_elem = result.select_one('.result__url')
                    snippet_elem = result.select_one('.result__snippet')
                    
                    if title_elem and link_elem:
                        results.append({
                            'title': title_elem.get_text(strip=True),
                            'url': link_elem.get_text(strip=True),
                            'content': snippet_elem.get_text(strip=True) if snippet_elem else '',
                            'engine': 'duckduckgo'
                        })
                    
                    if len(results) >= num_results:
                        break
                
                return results
                
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        return []
    
    def search_and_format(self, query: str) -> str:
        """Search and format results for the agent"""
        
        results = self.search(query)
        
        if not results:
            return f"No search results found for: {query}"
        
        formatted = f"=== WEB SEARCH RESULTS: {query} ===\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result['title']}**\n"
            formatted += f"   URL: {result['url']}\n"
            if result.get('content'):
                formatted += f"   {result['content']}\n"
            formatted += "\n"
        
        return formatted


WEB_SEARCH = WebSearch()