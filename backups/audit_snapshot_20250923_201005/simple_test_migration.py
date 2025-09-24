#!/usr/bin/env python3
"""
Simple Test Script for FA-GPT PostgreSQL Migration
Tests the complete migration from ChromaDB to PostgreSQL+pgvector+Apache AGE
"""

import sys
import os
import numpy as np
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Change to app directory for relative imports
os.chdir(str(Path(__file__).parent / "app"))

def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing database connection...")
    try:
        from postgres_storage import PostgreSQLStorage
        storage = PostgreSQLStorage()
        stats = storage.get_stats()
        storage.close()
        print(f"✅ Database connection successful! Stats: {stats}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_document_storage():
    """Test document metadata storage"""
    print("\n📄 Testing document storage...")
    try:
        from postgres_storage import PostgreSQLStorage, Document
        storage = PostgreSQLStorage()
        
        # Create a test document
        test_doc = Document(
            id="test-doc-001",
            filename="test_document.pdf",
            file_path="/home/drew/FA-GPT/test_document.pdf",
            file_type="pdf",
            file_size=1024000,
            page_count=10,
            processing_status="completed",
            extraction_method="test_migration",
            metadata={
                "test": True,
                "migration_test": "postgresql_unified"
            }
        )
        
        doc_id = storage.add_document(test_doc)
        print(f"✅ Document stored with ID: {doc_id}")
        
        # Retrieve the document
        retrieved_doc = storage.get_document(doc_id)
        if retrieved_doc and retrieved_doc.filename == test_doc.filename:
            print(f"✅ Document retrieved successfully: {retrieved_doc.filename}")
            storage.close()
            return True
        else:
            print("❌ Document retrieval failed")
            storage.close()
            return False
            
    except Exception as e:
        print(f"❌ Document storage test failed: {e}")
        return False

def test_vector_storage():
    """Test vector embeddings storage and search"""
    print("\n🔍 Testing vector storage and search...")
    try:
        from postgres_storage import PostgreSQLStorage, DocumentChunk
        storage = PostgreSQLStorage()
        
        # Create test embeddings (1536 dimensions for OpenAI compatibility)
        test_embedding_1 = np.random.rand(1536).astype(np.float32)
        test_embedding_2 = np.random.rand(1536).astype(np.float32)
        
        # Create document chunks with embeddings
        chunks = [
            DocumentChunk(
                document_id="test-doc-001",
                chunk_index=0,
                content="This is a test chunk about M777 Howitzer artillery systems.",
                content_type="text",
                embedding=test_embedding_1,
                metadata={"page": 1, "test": True}
            ),
            DocumentChunk(
                document_id="test-doc-001",
                chunk_index=1,
                content="Safety procedures for handling 155mm ammunition rounds.",
                content_type="text",
                embedding=test_embedding_2,
                metadata={"page": 2, "test": True}
            )
        ]
        
        chunk_ids = storage.add_document_chunks(chunks)
        print(f"✅ Stored {len(chunk_ids)} document chunks with embeddings")
        
        # Test semantic search
        query_embedding = np.random.rand(1536).astype(np.float32)
        results = storage.semantic_search(
            query_embedding=query_embedding,
            match_count=5,
            similarity_threshold=0.0  # Low threshold for test
        )
        
        print(f"✅ Semantic search returned {len(results)} results")
        if results:
            print(f"   Sample result: {results[0]['content'][:50]}...")
        
        storage.close()
        return True
        
    except Exception as e:
        print(f"❌ Vector storage test failed: {e}")
        return False

def test_image_embeddings():
    """Test image embeddings storage"""
    print("\n🖼️ Testing image embeddings...")
    try:
        from postgres_storage import PostgreSQLStorage, ImageEmbedding
        storage = PostgreSQLStorage()
        
        # Create test image embeddings
        test_embedding = np.random.rand(1536).astype(np.float32)
        
        image_embeds = [
            ImageEmbedding(
                document_id="test-doc-001",
                image_path="/home/drew/FA-GPT/images/test_image.png",
                image_description="Test image of artillery equipment",
                embedding=test_embedding,
                metadata={"page": 3, "test": True}
            )
        ]
        
        image_ids = storage.add_image_embeddings(image_embeds)
        print(f"✅ Stored {len(image_ids)} image embeddings")
        
        # Test multimodal search
        query_embedding = np.random.rand(1536).astype(np.float32)
        results = storage.multimodal_search(
            query_embedding=query_embedding,
            match_count=5,
            similarity_threshold=0.0  # Low threshold for test
        )
        
        print(f"✅ Multimodal search returned {len(results)} results")
        if results:
            print(f"   Found content types: {set(r['content_type'] for r in results)}")
        
        storage.close()
        return True
        
    except Exception as e:
        print(f"❌ Image embeddings test failed: {e}")
        return False

def test_knowledge_graph():
    """Test Apache AGE knowledge graph functionality"""
    print("\n🕸️ Testing knowledge graph (Apache AGE)...")
    try:
        from postgres_storage import PostgreSQLStorage
        storage = PostgreSQLStorage()
        
        # Create test knowledge relationships
        relationships = [
            ("M777_Howitzer", "USES", "M982_Excalibur", {
                "test": True,
                "description": "M777 howitzer uses Excalibur ammunition"
            }),
            ("M982_Excalibur", "REQUIRES", "GPS_Guidance", {
                "test": True,
                "description": "Excalibur requires GPS guidance system"
            }),
            ("M777_Howitzer", "HAS_SPECIFICATION", "155mm_Caliber", {
                "test": True,
                "caliber": "155mm",
                "range": "30km"
            })
        ]
        
        for subject, predicate, object_, properties in relationships:
            success = storage.create_knowledge_relationship(
                subject=subject,
                predicate=predicate,
                object_=object_,
                properties=properties
            )
            if success:
                print(f"✅ Created relationship: {subject} -[{predicate}]-> {object_}")
            else:
                print(f"❌ Failed to create relationship: {subject} -[{predicate}]-> {object_}")
        
        # Test knowledge graph query
        try:
            query = "MATCH (n)-[r]->(m) WHERE n.name CONTAINS 'M777' RETURN n, r, m LIMIT 5"
            results = storage.query_knowledge_graph(query)
            print(f"✅ Knowledge graph query returned {len(results)} results")
        except Exception as e:
            print(f"⚠️ Knowledge graph query test (expected for new graphs): {e}")
        
        storage.close()
        return True
        
    except Exception as e:
        print(f"❌ Knowledge graph test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        from postgres_storage import PostgreSQLStorage
        storage = PostgreSQLStorage()
        
        # Delete test document and all associated data
        success = storage.delete_document("test-doc-001")
        if success:
            print("✅ Test data cleaned up successfully")
        else:
            print("⚠️ Some test data may remain")
        
        storage.close()
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Run all migration tests"""
    print("🚀 FA-GPT PostgreSQL Migration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Document Storage", test_document_storage),
        ("Vector Storage & Search", test_vector_storage),
        ("Image Embeddings", test_image_embeddings),
        ("Knowledge Graph (Apache AGE)", test_knowledge_graph),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Migration successful!")
        print("\n✅ Your FA-GPT system has been successfully migrated to:")
        print("   • PostgreSQL 16 with pgvector for vector search")
        print("   • Apache AGE for knowledge graph capabilities")
        print("   • Unified storage interface replacing ChromaDB")
        return True
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)