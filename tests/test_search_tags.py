import unittest
from pathlib import Path
import sys
import os
import json
import numpy as np

# Add project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from knowledge_base_service import VectorDatabase, Document, EmbeddingAPI

# Mock EmbeddingAPI to avoid actual API calls
class MockEmbeddingAPI(EmbeddingAPI):
    def create_embedding(self, text: str, encoding_format: str = "float") -> list[float]:
        # A more representative mock.
        # The first dimension represents the query term "persona".
        # The second dimension represents the query term "karlach".
        # The third dimension represents the query term "wyll".
        vec = np.zeros(1024, dtype=np.float32)
        text = text.lower()
        
        if "persona" in text:
            vec[0] = 1.0
        if "karlach" in text:
            vec[1] = 1.0
        if "wyll" in text:
            vec[2] = 1.0
        
        # Add some noise to avoid identical vectors
        vec[10] = len(text) * 0.01 

        # Normalize the vector before returning, to mimic real-world embeddings
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

class TestSearchTags(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = project_root / 'tests' / 'test_data'
        # Ensure the directory is clean before starting
        if cls.db_path.exists():
            for f in cls.db_path.glob('*'):
                os.remove(f)
        else:
            cls.db_path.mkdir(exist_ok=True)
        
        # Override the data_dir for VectorDatabase and ensure it's empty
        cls.db = VectorDatabase(dimension=1024)
        cls.db.data_dir = cls.db_path
        cls.db.embedding_api = MockEmbeddingAPI() # Use the mock API

        # Explicitly clear data structures and save the empty state
        cls.db.vectors = []
        cls.db.documents = {}
        cls.db.document_ids = []
        cls.db.tag_index = {}
        cls.db._save_data()

        # Add test documents
        docs = [
            Document(id="doc1", content="karlach persona", tags=["role:karlach", "type:persona", "lang:zh"], metadata={}),
            Document(id="doc2", content="karlach levels", tags=["role:karlach", "type:levels"], metadata={}),
            Document(id="doc3", content="wyll persona", tags=["role:wyll", "type:persona"], metadata={}),
            Document(id="doc4", content="general info", tags=["type:general", "lang:zh"], metadata={})
        ]
        for doc in docs:
            cls.db.add_document(doc)

    @classmethod
    def tearDownClass(cls):
        # Clean up test data files
        for f in cls.db_path.glob('*'):
            os.remove(f)
        os.rmdir(cls.db_path)

    def test_tags_all_logic(self):
        """Test AND logic with tags_all."""
        results = self.db.search(query="karlach", tags_all=["role:karlach", "type:persona"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "doc1")

    def test_tags_any_logic(self):
        """Test OR logic with tags_any."""
        results = self.db.search(query="persona", tags_any=["role:karlach", "role:wyll"], top_k=2)
        result_ids = {res.id for res in results}
        self.assertEqual(len(result_ids), 2, f"Expected 2 results, but got {len(result_ids)}: {result_ids}")
        self.assertIn("doc1", result_ids)
        self.assertIn("doc3", result_ids)

    def test_combined_all_and_any(self):
        """Test combined AND and OR logic."""
        results = self.db.search(query="karlach", tags_all=["lang:zh"], tags_any=["type:persona", "type:general"])
        self.assertEqual(len(results), 2)
        result_ids = {res.id for res in results}
        self.assertIn("doc1", result_ids)
        self.assertIn("doc4", result_ids)

    def test_priority_boost(self):
        """Test that priority_tags boosts similarity score."""
        # Query that is closer to doc3 but should be boosted to prefer doc1
        # Mocked embedding is based on length and first char ascii value.
        query_close_to_doc3 = "wyll's story" # len 12, ord('w')=119
        # doc1 content "karlach persona" -> len 15, ord('k')=107
        # doc3 content "wyll persona" -> len 12, ord('w')=119
        
        # The query vector is much closer to doc3's vector.
        
        # Search without boost
        results_no_boost = self.db.search(query=query_close_to_doc3, top_k=2)
        self.assertEqual(results_no_boost[0].id, "doc3", "Without boost, doc3 should be closer")

        # Search with boost for "role:karlach"
        results_with_boost = self.db.search(query=query_close_to_doc3, top_k=2, priority_tags=["role:karlach"])
        
        # Debugging output
        print("\n--- Priority Boost Test ---")
        print(f"Query: {query_close_to_doc3}")
        print("Scores without boost:")
        for r in results_no_boost:
            print(f"  {r.id}: {self.db.search(query=query_close_to_doc3, top_k=4)}") # Re-run to get score info
        print("Scores with boost:")
        for r in results_with_boost:
            print(f"  {r.id}: {self.db.search(query=query_close_to_doc3, top_k=4, priority_tags=['role:karlach'])}")

        self.assertEqual(results_with_boost[0].id, "doc1", "With boost, doc1 should be ranked first")

    def test_backward_compatibility(self):
        """Test if old 'tags' parameter works like 'tags_all'."""
        results = self.db.search(query="karlach", tags=["role:karlach", "type:persona"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "doc1")

    def test_empty_result_on_no_match(self):
        """Test that an empty list is returned when no tags match."""
        results = self.db.search(query="karlach", tags_all=["nonexistent:tag"])
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
