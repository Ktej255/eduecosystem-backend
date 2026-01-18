from typing import List, Dict, Any, Optional
import google.generativeai as genai
import numpy as np
from app.core.config import settings
from app.services.gemini_service import gemini_service
import uuid
import logging

logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """
    A lightweight in-memory vector store for RAG.
    PROD TODO: Replace with ChromaDB or PGVector for scale.
    """
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        # Simple cache for embeddings to avoid re-computing
        self.embedding_cache: Dict[str, List[float]] = {}

    def add_document(self, text: str, metadata: Dict[str, Any] = None) -> str:
        doc_id = str(uuid.uuid4())
        # Clean text
        text = text.strip()
        if not text:
            return ""
            
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata or {},
            "embedding": None
        }
        return doc_id

    def embed_documents(self):
        """Batch embed documents that don't have embeddings yet."""
        texts_to_embed = []
        ids_to_embed = []

        for doc_id, doc in self.documents.items():
            if doc["embedding"] is None:
                texts_to_embed.append(doc["text"])
                ids_to_embed.append(doc_id)

        if not texts_to_embed:
            return

        try:
            # Use Gemini Embeddings
            # model="models/embedding-001"
            result = genai.embed_content(
                model="models/embedding-001",
                content=texts_to_embed,
                task_type="retrieval_document"
            )
            
            embeddings = result['embedding']
            
            for doc_id, emb in zip(ids_to_embed, embeddings):
                self.documents[doc_id]["embedding"] = np.array(emb)
                
        except Exception as e:
            logger.error(f"Embedding error: {e}")

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Find top-k relevant documents."""
        try:
            # Embed query
            result = genai.embed_content(
                model="models/embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = np.array(result['embedding'])

            scores = []
            for doc_id, doc in self.documents.items():
                if doc["embedding"] is None:
                    continue
                
                # Cosine similarity
                # (A . B) / (||A|| * ||B||)
                # Google embeddings are often normalized, but let's be safe
                doc_emb = doc["embedding"]
                score = np.dot(query_embedding, doc_emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb))
                scores.append((score, doc))

            # Sort by score descending
            scores.sort(key=lambda x: x[0], reverse=True)
            
            return [
                {"text": doc["text"], "metadata": doc["metadata"], "score": float(score)}
                for score, doc in scores[:k]
            ]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

class RagService:
    def __init__(self):
        self.store = SimpleVectorStore()
        # Pre-seed with some dummy context for demo if empty
        # In a real app, this would load from DB on startup
        self._seed_demo_content()

    def _seed_demo_content(self):
        """Seeds some UPSC/Graphotherapy content for the demo."""
        texts = [
           "Graphotherapy involves changing handwriting strokes to alter personality traits. For example, raising the t-bar can increase self-esteem and goals.",
           "The Preamble to the Constitution of India declares India to be a Sovereign, Socialist, Secular, Democratic Republic.",
           "In UPSC Mains, answer writing should follow the Introduction-Body-Conclusion format. Use diagrams and maps where possible.",
           "The t-bar crossing the stem at the top indicates high goals and strong willpower. A low t-bar indicates low self-esteem.",
           "Article 21 guarantees the Protection of Life and Personal Liberty. It has been expanded by the Supreme Court to include the Right to Privacy."
        ]
        for t in texts:
            self.store.add_document(t, {"source": "demo_seed"})
        self.store.embed_documents()

    def ingest(self, text: str, source: str):
        """Ingest text into the knowledge base."""
        # Simple chunking by sentence or fixed size
        # For MVP, just split by newlines or simplistic chunking
        chunks = [c.strip() for c in text.split('\n') if len(c.strip()) > 20]
        for chunk in chunks:
            self.store.add_document(chunk, {"source": source})
        self.store.embed_documents()

    def chat_with_guru(self, query: str, user_context: Optional[str] = None) -> Dict[str, Any]:
        """
        RAG Chat flow:
        1. Search vector store
        2. Construct prompt with context
        3. Generate response
        """
        relevant_docs = self.store.search(query, k=3)
        
        context_str = "\n".join([f"- {d['text']}" for d in relevant_docs])
        
        system_prompt = """You are the 'Guru', a wise and Socratic AI tutor for the Eduecosystem.
        Use the provided CONTEXT to answer the student's question.
        If the answer is in the context, cite it implicitly.
        If the answer is NOT in the context, use your general knowledge but mention that it's outside the provided materials.
        Be encouraging, concise, and use a teaching tone.
        """

        full_prompt = f"""CONTEXT:
{context_str}

STUDENT QUESTION:
{query}

ANSWER:"""

        response = gemini_service.generate_text(full_prompt, temperature=0.7)
        
        return {
            "answer": response,
            "sources": [d["text"][:50] + "..." for d in relevant_docs]
        }

rag_service = RagService()
