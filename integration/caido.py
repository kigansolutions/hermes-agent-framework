"""
prompt-orchestrator — Caido Integration
API wrapper for Caido web auditing toolkit
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class CaidoProject:
    id: str
    name: str

@dataclass
class CaidoRequest:
    id: str
    method: str
    url: str
    host: str
    path: str
    data: Optional[str]
    response_id: Optional[str]

@dataclass  
class CaidoResponse:
    id: str
    status_code: int
    content: str
    headers: Dict

class CaidoClient:
    """
    Python client for Caido API.
    Allows programmatic control of Caido for web testing.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", api_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token or os.environ.get('CAIDO_AUTH_TOKEN', '')
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    async def _graphql_request(self, query: str, variables: dict = None) -> dict:
        """Make GraphQL request to Caido"""
        async with aiohttp.ClientSession() as session:
            payload = {'query': query}
            if variables:
                payload['variables'] = variables
            
            async with session.post(
                f'{self.base_url}/graphql',
                json=payload,
                headers=self.headers
            ) as resp:
                return await resp.json()
    
    async def get_projects(self) -> List[CaidoProject]:
        """Get all projects"""
        query = '''
        query {
            projects {
                id
                name
            }
        }
        '''
        result = await self._graphql_request(query)
        return [CaidoProject(**p) for p in result.get('data', {}).get('projects', [])]
    
    async def get_current_project(self) -> CaidoProject:
        """Get current active project"""
        query = '''
        query {
            viewer {
                id
                activeProject {
                    id
                    name
                }
            }
        }
        '''
        result = await self._graphql_request(query)
        proj = result.get('data', {}).get('viewer', {}).get('activeProject', {})
        return CaidoProject(**proj) if proj else None
    
    async def create_request(self, method: str, url: str, data: str = None, 
                            headers: Dict = None) -> CaidoRequest:
        """Create and send a new request"""
        query = '''
        mutation CreateRequest($input: RequestInput!) {
            requestCreate(input: $input) {
                id
                method
                url
                host
                path
                data
            }
        }
        '''
        
        variables = {
            'input': {
                'method': method.upper(),
                'url': url,
                'data': data,
                'headers': headers or {}
            }
        }
        
        result = await self._graphql_request(query, variables)
        req = result.get('data', {}).get('requestCreate', {})
        return CaidoRequest(**req) if req else None
    
    async def replay_request(self, request_id: str) -> CaidoResponse:
        """Replay an existing request"""
        query = '''
        mutation ReplayRequest($id: ID!) {
            requestReplay(id: $id) {
                id
                response {
                    id
                    statusCode
                    content
                    headers
                }
            }
        }
        '''
        
        result = await self._graphql_request(query, {'id': request_id})
        resp_data = result.get('data', {}).get('requestReplay', {}).get('response', {})
        
        if resp_data:
            return CaidoResponse(
                id=resp_data.get('id', ''),
                status_code=resp_data.get('statusCode', 0),
                content=resp_data.get('content', ''),
                headers=resp_data.get('headers', {})
            )
        return None
    
    async def execute_automate(self, request_id: str, payloads: List[str], 
                              placeholder: str = "{{payload}}") -> List[Dict]:
        """Execute automate with payloads"""
        results = []
        
        for payload in payloads:
            modified_url = placeholder.replace("{{payload}}", payload)
            req = await self.create_request('GET', modified_url)
            
            if req:
                resp = await self.replay_request(req.id)
                results.append({
                    'payload': payload,
                    'request_id': req.id,
                    'status': resp.status_code if resp else 'error',
                    'response': resp.content[:500] if resp else ''
                })
        
        return results
    
    async def get_request_history(self, limit: int = 50) -> List[CaidoRequest]:
        """Get request history"""
        query = '''
        query GetRequests($limit: Int) {
            requests(limit: $limit) {
                id
                method
                url
                host
                path
            }
        }
        '''
        
        result = await self._graphql_request(query, {'limit': limit})
        reqs = result.get('data', {}).get('requests', [])
        return [CaidoRequest(**r) for r in reqs]
    
    async def create_scope_entry(self, url_pattern: str) -> bool:
        """Add URL to scope"""
        query = '''
        mutation AddToScope($pattern: String!) {
            scopeEntryCreate(pattern: $pattern) {
                id
            }
        }
        '''
        
        result = await self._graphql_request(query, {'pattern': url_pattern})
        return 'errors' not in result


class CaidoIntegration:
    """
    High-level integration for prompt-orchestrator.
    Provides tool-friendly interface.
    """
    
    def __init__(self):
        self.client = None
        self.connected = False
    
    def connect(self, base_url: str = "http://localhost:8080", api_token: str = None) -> str:
        """Connect to Caido instance"""
        self.client = CaidoClient(base_url, api_token)
        
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            project = loop.run_until_complete(self.client.get_current_project())
            if project:
                self.connected = True
                return f"Connected to Caido project: {project.name}"
        except Exception as e:
            return f"Failed to connect: {str(e)}"
        
        return "Connected (no active project)"
    
    def send_request(self, method: str, url: str, data: str = None) -> str:
        """Send a request through Caido"""
        if not self.client:
            return "Error: Not connected to Caido"
        
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            req = loop.run_until_complete(
                self.client.create_request(method, url, data)
            )
            
            resp = loop.run_until_complete(
                self.client.replay_request(req.id)
            )
            
            if resp:
                return f"""
=== Request Sent ===
Method: {method}
URL: {url}

=== Response ===
Status: {resp.status_code}
Headers: {json.dumps(resp.headers, indent=2)}

Content:
{resp.content[:2000]}
"""
        except Exception as e:
            return f"Error: {str(e)}"
        
        return "Request sent"
    
    def fuzz_parameters(self, url: str, param_name: str, payloads: List[str]) -> str:
        """Fuzz a parameter with payloads"""
        if not self.client:
            return "Error: Not connected to Caido"
        
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        base_url = f"{url}?{param_name}={{{{payload}}}}"
        
        try:
            results = loop.run_until_complete(
                self.client.execute_automate_url(base_url, payloads)
            )
            
            output = f"=== Fuzzing Results ===\n\n"
            for r in results[:20]:
                output += f"[{r['status']}] {r['payload']}\n"
                if r.get('response'):
                    output += f"  Response: {r['response'][:200]}...\n"
            
            return output
        except Exception as e:
            return f"Error: {str(e)}"
    
    def add_to_scope(self, pattern: str) -> str:
        """Add URL pattern to scope"""
        if not self.client:
            return "Error: Not connected to Caido"
        
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                self.client.create_scope_entry(pattern)
            )
            return f"Added to scope: {pattern}" if success else "Failed to add to scope"
        except Exception as e:
            return f"Error: {str(e)}"


CAIDO = CaidoIntegration()


# Standalone functions for tool calling
async def caido_send_request(method: str, url: str, data: str = None) -> str:
    """Tool: Send request through Caido"""
    return CAIDO.send_request(method, url, data)

async def caido_add_scope(pattern: str) -> str:
    """Tool: Add URL pattern to Caido scope"""
    return CAIDO.add_to_scope(pattern)

async def caido_get_history(limit: int = 50) -> str:
    """Tool: Get Caido request history"""
    if not CAIDO.client:
        return "Error: Not connected to Caido"
    
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        requests = loop.run_until_complete(
            CAIDO.client.get_request_history(limit)
        )
        
        output = "=== Caido Request History ===\n\n"
        for req in requests[:20]:
            output += f"{req.method} {req.url}\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"