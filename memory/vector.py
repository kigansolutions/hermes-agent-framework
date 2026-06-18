"""
prompt-orchestrator — FAISS Vector Memory
==========================================
Semantic search over memories using embeddings.
"""

import os
import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class VectorMemory:
    """
    FAISS-based vector memory for semantic search.
    Stores memories as embeddings and enables similarity search.
    """
    
    def __init__(self, dimension: int = 384, db_path: str = "./data/aios.db"):
        self.db_path = db_path
        self.dimension = dimension
        self.index = None
        self.id_to_memory = {}
        self.next_id = 0
        self.embedding_model = None
        
        if FAISS_AVAILABLE:
            self._init_index()
        
        self._init_tables()
        self._load_existing_memories()
        self._init_embedding_model()
    
    def _init_index(self):
        """Initialize FAISS index"""
        self.index = faiss.IndexFlatL2(self.dimension)
    
    def _init_embedding_model(self):
        """Load sentence transformer for embeddings"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Embedding model loaded: all-MiniLM-L6-v2")
            except Exception as e:
                print(f"Failed to load embedding model: {e}")
    
    def _init_tables(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vector_memories (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_existing_memories(self):
        """Load existing memories into index"""
        if not FAISS_AVAILABLE:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, content FROM vector_memories')
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            memory_id, content = row
            embedding = self._get_embedding(content)
            if embedding is not None:
                self.index.add(np.array([embedding]).astype('float32'))
                self.id_to_memory[memory_id] = content
                self.next_id = max(self.next_id, memory_id + 1)
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text"""
        if self.embedding_model is None:
            return np.random.randn(self.dimension).astype('float32')
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def add(self, content: str, category: str = "general", metadata: dict = None) -> int:
        """Add a memory to the vector store"""
        
        if not FAISS_AVAILABLE:
            return -1
        
        memory_id = self.next_id
        self.next_id += 1
        
        embedding = self._get_embedding(content)
        if embedding is not None:
            self.index.add(np.array([embedding]).astype('float32'))
            self.id_to_memory[memory_id] = content
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vector_memories (id, content, category, metadata)
            VALUES (?, ?, ?, ?)
        ''', (memory_id, content, category, json.dumps(metadata) if metadata else None))
        
        conn.commit()
        conn.close()
        
        return memory_id
    
    def search(self, query: str, k: int = 5, category: str = None) -> List[Dict]:
        """Search for similar memories"""
        
        if not FAISS_AVAILABLE or self.index.ntotal == 0:
            return []
        
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return []
        
        search_k = min(k * 2, self.index.ntotal)
        
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'),
            search_k
        )
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            
            memory_id = int(idx) + 1
            if memory_id not in self.id_to_memory:
                for mid, content in self.id_to_memory.items():
                    if mid == idx:
                        memory_id = mid
                        break
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = 'SELECT id, content, category, metadata, access_count FROM vector_memories'
            params = []
            if category:
                query += ' WHERE category = ?'
                params.append(category)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                if row[0] == memory_id:
                    results.append({
                        'id': row[0],
                        'content': row[1],
                        'category': row[2],
                        'metadata': json.loads(row[3]) if row[3] else {},
                        'access_count': row[4],
                        'distance': float(dist)
                    })
                    break
        
        return results[:k]
    
    def get_memories_by_category(self, category: str) -> List[Dict]:
        """Get all memories in a category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, content, metadata, created_at, access_count
            FROM vector_memories
            WHERE category = ?
            ORDER BY created_at DESC
        ''', (category,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'content': r[1],
            'metadata': json.loads(r[2]) if r[2] else {},
            'created_at': r[3],
            'access_count': r[4]
        } for r in rows]
    
    def update_access(self, memory_id: int):
        """Update access count for a memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE vector_memories
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), memory_id))
        
        conn.commit()
        conn.close()
    
    def delete(self, memory_id: int):
        """Delete a memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM vector_memories WHERE id = ?', (memory_id,))
        
        conn.commit()
        conn.close()
        
        if memory_id in self.id_to_memory:
            del self.id_to_memory[memory_id]


VECTOR_MEMORY = VectorMemory()