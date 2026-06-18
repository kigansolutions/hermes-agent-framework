"""
PromptOrchestrator Knowledge Base Manager
Comprehensive security knowledge for workflow execution
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

class KnowledgeBase:
    """
    Comprehensive knowledge base for security testing.
    Includes OWASP standards and more.
    """
    
    def __init__(self, kb_dir: str = "./knowledge"):
        self.kb_dir = Path(kb_dir)
        self.documents = {}
        self._load_documents()
        
        # Index documents by category
        self.by_category = {
            'web': [],
            'api': [],
            'llm': [],
            'smart-contract': [],
            'methodology': [],
            'payloads': []
        }
        self._index_by_category()
    
    def _load_documents(self):
        """Load knowledge documents"""
        
        if not self.kb_dir.exists():
            self.kb_dir = Path(__file__).parent.parent / "knowledge"
            if not self.kb_dir.exists():
                print(f"Knowledge base not found")
                return
        
        for doc_file in self.kb_dir.glob("**/*.md"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                relative_path = str(doc_file.relative_to(self.kb_dir))
                doc_name = relative_path.replace('.md', '').replace('\\', '/')
                self.documents[doc_name] = content
                
            except Exception as e:
                print(f"Failed to load {doc_file}: {e}")
    
    def _index_by_category(self):
        """Index documents by category"""
        
        for name in self.documents.keys():
            if 'owasp-web' in name or 'owasp-top-10' in name:
                self.by_category['web'].append(name)
            elif 'owasp-api' in name:
                self.by_category['api'].append(name)
            elif 'owasp-llm' in name:
                self.by_category['llm'].append(name)
            elif 'owasp-smart' in name or 'smart-contract' in name:
                self.by_category['smart-contract'].append(name)
    
    def get_document(self, name: str) -> Optional[str]:
        """Get a specific document"""
        return self.documents.get(name)
    
    def get_by_category(self, category: str) -> Dict[str, str]:
        """Get all documents in a category"""
        docs = self.by_category.get(category, [])
        return {d: self.documents.get(d, '') for d in docs}
    
    def search(self, query: str) -> List[Dict]:
        """Search knowledge base"""
        results = []
        query_lower = query.lower()
        
        for name, content in self.documents.items():
            if query_lower in content.lower():
                # Get category
                category = 'general'
                for cat, docs in self.by_category.items():
                    if name in docs:
                        category = cat
                        break
                
                results.append({
                    'name': name,
                    'category': category,
                    'preview': content[:300]
                })
        
        return results
    
    # === Convenience Methods ===
    
    def get_owasp_web(self) -> str:
        """Get OWASP Top 10 Web"""
        return self.documents.get('owasp-web', 
               self.documents.get('owasp-top-10', 'Not found'))
    
    def get_owasp_api(self) -> str:
        """Get OWASP API Security Top 10"""
        return self.documents.get('owasp-api', 'Not found')
    
    def get_owasp_llm(self) -> str:
        """Get OWASP Top 10 for LLM"""
        return self.documents.get('owasp-llm', 'Not found')
    
    def get_owasp_smart_contract(self) -> str:
        """Get OWASP Smart Contract Top 10"""
        return self.documents.get('owasp-smart-contract', 'Not found')
    
    def get_owasp_all(self) -> str:
        """Get all OWASP documents combined"""
        parts = []
        
        web = self.get_owasp_web()
        if web and 'not found' not in web.lower():
            parts.append(web)
        
        api = self.get_owasp_api()
        if api and 'not found' not in api.lower():
            parts.append(api)
        
        llm = self.get_owasp_llm()
        if llm and 'not found' not in llm.lower():
            parts.append(llm)
        
        sc = self.get_owasp_smart_contract()
        if sc and 'not found' not in sc.lower():
            parts.append(sc)
        
        return '\n\n---\n\n'.join(parts)
    
    def list_documents(self) -> List[Dict]:
        """List all documents with metadata"""
        result = []
        
        for name in self.documents.keys():
            category = 'general'
            for cat, docs in self.by_category.items():
                if name in docs:
                    category = cat
                    break
            
            result.append({
                'name': name,
                'category': category,
                'size': len(self.documents[name])
            })
        
        return result
    
    def get_reference(self, vuln_type: str) -> str:
        """Get quick reference for vulnerability type"""
        
        query = vuln_type.lower()
        results = self.search(query)
        
        if results:
            return self.documents.get(results[0]['name'], '')
        
        return f"No reference found for: {vuln_type}"


# Create global instance
KNOWLEDGE_BASE = KnowledgeBase()