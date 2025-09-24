# app/rag_core.py
"""
Retrieval-Augmented Generation (RAG) Core for FA-GPT

This module implements the complete RAG pipeline for answering questions
about Field Artillery documents using multimodal retrieval and a consolidated
Vision-Language Model for all AI operations.

RAG Pipeline:
1. Query Understanding: Analyze user query to determine retrieval strategy
2. Multimodal Retrieval: Search for relevant text and images using embeddings
3. VLM Reranking: Use vision-language model to intelligently rank results
4. Knowledge Graph Augmentation: Add relevant entities and relationships
5. Response Generation: Generate comprehensive answers with citations

The system uses:
- PostgreSQL with pgvector for vector similarity search and content retrieval
- Apache AGE extension for knowledge graph entity relationships
- Qwen 2.5 VL for all text analysis, image analysis, and response generation
- Nomic Embed Text for local embedding generation
- IBM Granite-Docling-258M for enhanced document extraction

All processing happens locally without external API calls, using a single
Vision-Language Model for consistent reasoning across all pipeline stages.
"""

import json
import base64
from typing import List, Dict, Tuple
import numpy as np

from .connectors import get_ollama_client, get_storage_client
from .multimodal_embeddings import get_multimodal_embedder
from .config import settings

def get_rag_response(query: str) -> Tuple[str, List[str], Dict]:
    """
    Main RAG pipeline with local Vision-Language Model support.
    
    Processes a user query through the complete RAG pipeline to generate
    a comprehensive answer with supporting visual and textual evidence.
    
    Args:
        query (str): User question about Field Artillery documents
        
    Returns:
        Tuple containing:
        - str: Generated response with citations and analysis
        - List[str]: Base64-encoded images that support the answer
        - Dict: Metadata about the retrieval and generation process
        
    Pipeline Steps:
        1. Query Understanding: Determine if query needs images, KG data, etc.
        2. Multimodal Retrieval: Find relevant text and images using embeddings
        3. VLM Reranking: Score relevance using vision-language model
        4. Knowledge Graph: Add entity relationships if relevant
        5. Response Generation: Create comprehensive answer with sources
        
    Example:
        response, images, metadata = get_rag_response("How does the M777 howitzer work?")
    """
    client = get_ollama_client()
    
    # 1. Query Understanding (using local LLM)
    query_intent = analyze_query_intent(query, client)
    
    # 2. Multi-modal retrieval
    retrieved = retrieve_multimodal_content(query, query_intent)
    
    # 3. VLM-based reranking
    reranked = rerank_with_local_vlm(query, retrieved, client)
    
    # 4. Knowledge Graph augmentation
    kg_context = get_kg_context(query) if query_intent.get('needs_kg', False) else []
    
    # 5. Generate response with VLM
    response, sources = generate_vlm_response(query, reranked[:5], kg_context, client)
    
    # Extract images for display
    source_images = [r['image_data'] for r in reranked[:3] if r.get('image_data')]
    
    # Compile metadata
    metadata = {
        'query_intent': query_intent,
        'retrieved_count': len(retrieved),
        'kg_nodes': len(kg_context)
    }
    
    return response, source_images, metadata

def analyze_query_intent(query: str, client) -> Dict:
    """
    Analyze user query to determine optimal retrieval strategy.
    
    Uses the local LLM to understand what type of information the user
    is seeking and how the system should search for relevant content.
    
    Args:
        query (str): User's question
        client: Ollama client for LLM inference
        
    Returns:
        Dict with analysis results:
        - type: "factual", "procedural", "visual", or "comparative"
        - needs_kg: bool indicating if knowledge graph data would help
        - needs_images: bool indicating if visual content is relevant
        - key_entities: list of important entities mentioned
        
    Query Types:
        - factual: Seeking specific facts or specifications
        - procedural: Asking about processes or step-by-step instructions
        - visual: Requires diagrams, images, or visual explanation
        - comparative: Comparing different systems or options
    """
    prompt = """Analyze this query and return a JSON object with:
    - "type": "factual" or "procedural" or "visual" or "comparative"
    - "needs_kg": true/false (needs knowledge graph data)
    - "needs_images": true/false (needs visual content)
    - "key_entities": [list of key entities mentioned]
    
    Query: {query}
    """
    
    try:
        response = client.chat(
            model=settings.vlm_model,  # Using consolidated VLM for all operations
            messages=[{'role': 'user', 'content': prompt.format(query=query)}],
            format='json',
            options={'temperature': 0.1}
        )
        return json.loads(response['message']['content'])
    except:
        return {'type': 'factual', 'needs_kg': True, 'needs_images': True, 'key_entities': []}

def retrieve_multimodal_content(query: str, intent: Dict) -> List[Dict]:
    """
    Retrieve relevant content using vector similarity search on Docling-parsed data.
    
    Searches the PostgreSQL vector database for content similar to the user's
    query, filtering by content type based on the query intent analysis.
    
    Args:
        query (str): User's question
        intent (Dict): Query intent analysis from analyze_query_intent()
        
    Returns:
        List[Dict]: Retrieved content items with metadata:
        - id: Unique element identifier
        - source_doc: Source document filename
        - element_type: text, image, table, etc.
        - content: Text content (for text elements)
        - image_data: Binary image data (for image elements)
        - metadata: Additional element information
        - similarity: Cosine similarity score to query
        
    Search Strategy:
        - Always searches text, table, and title elements
        - Includes image elements if intent.needs_images is True
        - Uses cosine similarity with query embedding
        - Returns top 30 matches for reranking
    """
    embedder = get_multimodal_embedder()
    query_embedding = embedder.embed_texts([query])[0]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build dynamic query based on intent
    element_types = ['text', 'table', 'title']
    if intent.get('needs_images'):
        element_types.append('image')
    
    # Retrieve with similarity search
    cur.execute("""
        SELECT 
            id, source_doc, element_type, content, image_data, metadata,
            1 - (embedding <=> %s) as similarity
        FROM fa_gpt_documents
        WHERE element_type = ANY(%s)
        ORDER BY embedding <=> %s
        LIMIT 30
    """, (query_embedding.tolist(), element_types, query_embedding.tolist()))
    
    results = []
    for row in cur.fetchall():
        results.append({
            'id': row[0],
            'source_doc': row[1],
            'element_type': row[2],
            'content': row[3],
            'image_data': row[4],
            'metadata': row[5],
            'similarity': row[6]
        })
    
    cur.close()
    conn.close()
    return results

def rerank_with_local_vlm(query: str, results: List[Dict], client) -> List[Dict]:
    """
    Use local Vision-Language Model for intelligent content reranking.
    
    Applies semantic reranking to retrieved content using AI models to
    better understand relevance beyond simple vector similarity.
    
    Args:
        query (str): User's original question
        results (List[Dict]): Retrieved content from vector search
        client: Ollama client for model inference
        
    Returns:
        List[Dict]: Reranked results with additional scoring:
        - vlm_score: Relevance score from AI analysis (0.0-1.0)
        - vlm_reason: Explanation of relevance (for images)
        - final_score: Combined similarity + AI score
        
    Reranking Strategy:
        - Images: VLM analyzes visual content relevance to query
        - Text: LLM evaluates content relevance and usefulness
        - Final score: 40% vector similarity + 60% AI relevance score
        - Results sorted by final_score descending
        
    This ensures the most semantically relevant content appears first,
    not just the most similar by embedding distance.
    """
    
    for result in results:
        if result['element_type'] == 'image' and result['image_data']:
            # Use VLM to analyze image relevance
            img_base64 = base64.b64encode(result['image_data']).decode()
            
            prompt = f"""Analyze this image in the context of the query: "{query}"
            Rate its relevance from 0.0 to 1.0 and explain why.
            Return JSON: {{"score": 0.0-1.0, "reason": "explanation"}}"""
            
            try:
                response = client.chat(
                    model=settings.vlm_model,
                    messages=[{
                        'role': 'user',
                        'content': prompt,
                        'images': [img_base64]
                    }],
                    format='json',
                    options={'temperature': 0.1}
                )
                score_data = json.loads(response['message']['content'])
                result['vlm_score'] = score_data.get('score', 0.5)
                result['vlm_reason'] = score_data.get('reason', '')
            except:
                result['vlm_score'] = 0.5
        else:
            # Text scoring with LLM
            prompt = f"""Rate the relevance of this content to the query.
            Query: "{query}"
            Content Type: {result['element_type']}
            Content: {result.get('content', '')[:500]}
            
            Return JSON: {{"score": 0.0-1.0}}"""
            
            try:
                response = client.chat(
                    model=settings.vlm_model,  # Using consolidated VLM for text scoring
                    messages=[{'role': 'user', 'content': prompt}],
                    format='json',
                    options={'temperature': 0.1}
                )
                score_data = json.loads(response['message']['content'])
                result['vlm_score'] = score_data.get('score', 0.5)
            except:
                result['vlm_score'] = 0.5
    
    # Combine similarity and VLM scores
    for result in results:
        result['final_score'] = (
            0.4 * result.get('similarity', 0) + 
            0.6 * result.get('vlm_score', 0.5)
        )
    
    return sorted(results, key=lambda x: x['final_score'], reverse=True)

def get_kg_context(query: str) -> List[Dict]:
    """
    Retrieve relevant knowledge graph context from PostgreSQL with Apache AGE.
    
    Searches the knowledge graph for entities and relationships that
    may be relevant to the user's query, providing structured context
    that enhances the RAG response.
    
    Args:
        query (str): User's question
        
    Returns:
        List[Dict]: Knowledge graph context items:
        - entity: Dict with entity properties (id, type, etc.)
        - connections: List of related entities and relationship types
        
    Search Strategy:
        - Finds nodes where entity name contains query terms (case-insensitive)
        - Retrieves connected nodes and relationship types
        - Limits to top 10 most relevant entities
        - Includes source document and page references
        
    Example Context:
        [
            {
                "entity": {"name": "M777_Howitzer", "type": "WeaponSystem", "caliber": "155mm"},
                "connections": [
                    {"relationship": "USES", "node": {"name": "M795_Projectile"}},
                    {"relationship": "HAS_SPECIFICATION", "node": {"name": "Range_30km"}}
                ]
            }
        ]
    """
    storage = get_storage_client()
    kg_context = []
    
    try:
        # Search for entities related to the query using Apache AGE
        cypher_query = f"""
            MATCH (n)
            WHERE n.name CONTAINS '{query.lower()}'
            OPTIONAL MATCH (n)-[r]-(connected)
            RETURN n, collect({{relationship: type(r), node: connected}}) as connections
            LIMIT 10
        """
        
        results = storage.query_knowledge_graph(cypher_query)
        
        for result in results:
            try:
                # Parse the Apache AGE result format
                if 'result' in result:
                    kg_context.append({
                        'entity': {'name': 'knowledge_entity', 'type': 'entity'},
                        'connections': [],
                        'raw_result': result['result']
                    })
            except Exception as e:
                print(f"Error parsing knowledge graph result: {e}")
                continue
    
    except Exception as e:
        print(f"Error retrieving knowledge graph context: {e}")
    finally:
        storage.close()
    
    return kg_context
    
    with driver.session() as session:
        # Find relevant nodes and relationships
        result = session.run("""
            MATCH (n)
            WHERE toLower(n.id) CONTAINS toLower($query)
            OPTIONAL MATCH (n)-[r]-(connected)
            RETURN n, collect({relationship: type(r), node: connected}) as connections
            LIMIT 10
        """, query=query)
        
        for record in result:
            node = dict(record['n'])
            connections = record['connections']
            kg_context.append({
                'entity': node,
                'connections': connections
            })
    
    driver.close()
    return kg_context

def generate_vlm_response(query: str, contexts: List[Dict], kg_context: List[Dict], client) -> Tuple[str, List[Dict]]:
    """
    Generate comprehensive response using local Vision-Language Model.
    
    Combines retrieved text and image content with knowledge graph context
    to generate a detailed, well-sourced answer to the user's question.
    
    Args:
        query (str): User's original question
        contexts (List[Dict]): Top-ranked content from retrieval and reranking
        kg_context (List[Dict]): Relevant knowledge graph entities and relationships
        client: Ollama client for model inference
        
    Returns:
        Tuple containing:
        - str: Generated response with citations and detailed analysis
        - List[Dict]: Source contexts used in generation
        
    Response Generation Strategy:
        - Separates text and image content for processing
        - Builds comprehensive context string with source attribution
        - Adds knowledge graph entities and relationships
        - Uses VLM for image-aware responses when images are present
        - Falls back to LLM for text-only responses
        - Includes proper source citations and references
        
    Context Format:
        - Text: "[TYPE from SOURCE]: content"
        - Knowledge Graph: Entity properties and connections
        - Images: Provided as base64 with source attribution
        
    Model Selection:
        - VLM (qwen2.5vl:7b): When relevant images are available
        - LLM (qwen2.5:7b): For text-only responses
        - Temperature 0.3: Balance between accuracy and creativity
    """
    
    # Prepare context
    text_context = []
    image_contexts = []
    
    for ctx in contexts:
        if ctx['element_type'] == 'image' and ctx['image_data']:
            image_contexts.append({
                'data': ctx['image_data'],
                'source': ctx['source_doc'],
                'reason': ctx.get('vlm_reason', '')
            })
        else:
            text_context.append({
                'type': ctx['element_type'],
                'content': ctx.get('content', ''),
                'source': ctx['source_doc'],
                'metadata': ctx.get('metadata', {})
            })
    
    # Build comprehensive prompt
    system_prompt = """You are an expert U.S. Army Field Artillery assistant with access to technical manuals and visual materials.
    Provide accurate, detailed responses based ONLY on the provided context. Always cite sources."""
    
    # Format text context
    context_str = "\n\n".join([
        f"[{ctx['type'].upper()} from {ctx['source']}]:\n{ctx['content']}"
        for ctx in text_context
    ])
    
    # Add KG context if available
    if kg_context:
        kg_str = "\n\nKnowledge Graph Context:\n"
        for kg in kg_context:
            entity = kg['entity']
            kg_str += f"- Entity: {entity.get('id')} (Type: {entity.get('type', 'Unknown')})\n"
            if kg['connections']:
                kg_str += "  Connections: " + ", ".join([
                    f"{c['relationship']} -> {c['node'].get('id', 'Unknown')}"
                    for c in kg['connections'][:3]
                ]) + "\n"
        context_str += kg_str
    
    # Prepare message
    user_message = f"""Based on the following context, answer this question: {query}
    
    Context:
    {context_str}
    
    Provide a comprehensive answer with source citations."""
    
    # Always use VLM for response generation (handles both text and images)
    messages = [{'role': 'system', 'content': system_prompt}]
    
    # Add images if available
    if image_contexts:
        img_base64 = base64.b64encode(image_contexts[0]['data']).decode()
        user_message += f"\n\nRelevant visual material from {image_contexts[0]['source']} is provided."
        messages.append({'role': 'user', 'content': user_message, 'images': [img_base64]})
    else:
        messages.append({'role': 'user', 'content': user_message})
    
    response = client.chat(
        model=settings.vlm_model,  # Consolidated VLM handles both text and multimodal
        messages=messages,
        options={'temperature': 0.3}
    )
    
    return response['message']['content'], contexts[:5]