#!/usr/bin/env python3
"""
RAG Query Engine with Cross-Encoder Reranking for FA-GPT

This script implements a comprehensive RAG workflow that:
1. Embeds user queries using the same embedding model as ingestion
2. Retrieves top candidates from PostgreSQL using vector similarity
3. Uses a cross-encoder model for intelligent reranking
4. Builds optimized context for final LLM generation

Usage:
    python query_rag.py

The script will prompt for queries and show the complete retrieval and reranking
pipeline results, allowing you to test the entire RAG system.
"""

import os
import sys
import psycopg2
import torch
import json
import base64
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

class RAGQueryEngine:
    """
    Complete RAG query engine with cross-encoder reranking for maximum accuracy.
    """
    
    def __init__(self):
        """Initialize all required models and database connections."""
        print("🚀 Initializing RAG Query Engine...")
        
        # Load embedding model (same as used during ingestion)
        print("📥 Loading text embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load cross-encoder reranker
        print("🔄 Loading cross-encoder reranker...")
        self.reranker = CrossEncoder('BAAI/bge-reranker-base')
        
        print("✅ RAG Query Engine initialized successfully!")
    
    def get_postgres_connection(self):
        """Get PostgreSQL database connection."""
        return psycopg2.connect(settings.postgres_uri)
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed the user query using the same model as document ingestion.
        
        Args:
            query: User question string
            
        Returns:
            Query embedding vector
        """
        return self.embedding_model.encode([query])[0]
    
    def retrieve_candidates(self, query: str, top_k: int = 25) -> List[Dict]:
        """
        Retrieve top candidate chunks from PostgreSQL using vector similarity.
        
        Args:
            query: User question
            top_k: Number of candidates to retrieve
            
        Returns:
            List of candidate documents with metadata
        """
        print(f"🔍 Retrieving top {top_k} candidates...")
        
        query_embedding = self.embed_query(query)
        
        conn = self.get_postgres_connection()
        cur = conn.cursor()
        
        # Search across all content types for maximum coverage
        cur.execute("""
            SELECT 
                id, 
                source_doc, 
                element_type, 
                content, 
                page, 
                bbox, 
                image_data,
                vml_analysis,
                metadata,
                1 - (embedding <=> %s) as similarity
            FROM fa_gpt_documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s
            LIMIT %s
        """, (query_embedding.tolist(), query_embedding.tolist(), top_k))
        
        candidates = []
        for row in cur.fetchall():
            candidate = {
                'id': row[0],
                'source_doc': row[1],
                'element_type': row[2],
                'content': row[3] or '',
                'page': row[4],
                'bbox': row[5],
                'image_data': row[6],
                'vml_analysis': row[7],
                'metadata': row[8],
                'similarity': row[9]
            }
            candidates.append(candidate)
        
        cur.close()
        conn.close()
        
        print(f"📋 Retrieved {len(candidates)} candidates")
        return candidates
    
    def rerank_with_cross_encoder(self, query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Use cross-encoder to rerank candidates for maximum relevance.
        
        Args:
            query: User question
            candidates: List of retrieved candidates
            top_k: Number of top results to return after reranking
            
        Returns:
            Reranked and filtered list of most relevant candidates
        """
        print("🎯 Reranking candidates with cross-encoder...")
        
        # Prepare query-document pairs for the cross-encoder
        pairs = []
        valid_candidates = []
        
        for candidate in candidates:
            # Create meaningful text representation for each candidate
            if candidate['element_type'] == 'image' and candidate.get('vml_analysis'):
                # Use VML analysis for images if available
                text_content = json.dumps(candidate['vml_analysis'])
            else:
                # Use direct content for text elements
                text_content = candidate['content']
            
            if text_content and len(text_content.strip()) > 10:  # Only valid content
                pairs.append([query, text_content[:512]])  # Limit text length
                valid_candidates.append(candidate)
        
        if not pairs:
            print("⚠️  No valid candidates for reranking")
            return []
        
        # Get cross-encoder scores
        print(f"🔢 Computing relevance scores for {len(pairs)} pairs...")
        scores = self.reranker.predict(pairs)
        
        # Add scores to candidates and sort
        for i, candidate in enumerate(valid_candidates):
            candidate['rerank_score'] = float(scores[i])
        
        # Sort by reranking score (descending) and take top_k
        reranked = sorted(valid_candidates, key=lambda x: x['rerank_score'], reverse=True)[:top_k]
        
        print(f"🏆 Selected top {len(reranked)} candidates after reranking")
        return reranked
    
    def build_prompt(self, query: str, reranked_chunks: List[Dict]) -> str:
        """
        Build the final prompt context from reranked chunks.
        
        Args:
            query: User question
            reranked_chunks: Top reranked document chunks
            
        Returns:
            Formatted prompt with context for LLM
        """
        context_parts = []
        
        for i, chunk in enumerate(reranked_chunks, 1):
            context_part = f"[SOURCE {i}: {chunk['source_doc']}, Page {chunk['page']}, Type: {chunk['element_type']}]"
            
            if chunk['element_type'] == 'image' and chunk.get('vml_analysis'):
                context_part += f"\nImage Analysis: {json.dumps(chunk['vml_analysis'], indent=2)}"
            else:
                context_part += f"\nContent: {chunk['content'][:1000]}"
            
            context_part += f"\nRelevance Score: {chunk['rerank_score']:.3f}"
            context_parts.append(context_part)
        
        context = "\n\n" + "\n\n".join(context_parts)
        
        prompt = f"""Based on the following context from U.S. Army Field Artillery documents, please answer this question: {query}

CONTEXT:{context}

Please provide a comprehensive answer based on the provided context, citing specific sources by their SOURCE numbers.
"""
        
        return prompt
    
    def query_pipeline(self, query: str) -> Tuple[str, List[Dict]]:
        """
        Complete RAG pipeline from query to final context.
        
        Args:
            query: User question
            
        Returns:
            Tuple of (final_prompt, reranked_candidates)
        """
        print(f"\n{'='*60}")
        print(f"🎯 QUERY: {query}")
        print(f"{'='*60}")
        
        # Step 1: Retrieve candidates
        candidates = self.retrieve_candidates(query, top_k=25)
        
        # Step 2: Rerank with cross-encoder
        reranked = self.rerank_with_cross_encoder(query, candidates, top_k=5)
        
        # Step 3: Build final prompt
        final_prompt = self.build_prompt(query, reranked)
        
        return final_prompt, reranked

def main():
    """
    Interactive RAG query testing interface.
    """
    print("🤖 FA-GPT RAG Query Engine with Cross-Encoder Reranking")
    print("=" * 60)
    
    try:
        # Initialize the RAG engine
        rag_engine = RAGQueryEngine()
        
        print("\n💡 Enter your questions about Field Artillery documents.")
        print("💡 Type 'quit' to exit.\n")
        
        while True:
            query = input("❓ Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            try:
                # Run the complete RAG pipeline
                final_prompt, reranked_results = rag_engine.query_pipeline(query)
                
                print("\n" + "="*60)
                print("📋 FINAL CONTEXT FOR LLM:")
                print("="*60)
                print(final_prompt)
                
                print("\n" + "="*60)
                print("📊 RERANKING RESULTS SUMMARY:")
                print("="*60)
                for i, result in enumerate(reranked_results, 1):
                    print(f"{i}. {result['source_doc']} (Page {result['page']}) - Score: {result['rerank_score']:.3f}")
                    print(f"   Type: {result['element_type']}")
                    print(f"   Content Preview: {result['content'][:100]}...")
                    print()
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                import traceback
                traceback.print_exc()
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to initialize RAG engine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()