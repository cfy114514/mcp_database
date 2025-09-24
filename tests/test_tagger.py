import unittest
from pathlib import Path
import sys
import os
import json

# Add project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.tagger import Tagger

class TestTagger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a dummy schema for testing
        cls.schema_path = project_root / 'tests' / 'test_schema.json'
        cls.test_schema = {
            "path_map": {
                "persona.txt": ["role:karlach", "type:persona"],
                "xingfa": ["domain:legal", "type:law"]
            },
            "keyword_map": {
                "地狱引擎": ["topic:infernal_engine"],
                "关卡": ["type:levels"]
            },
            "regex_map": {
                 "第[一-十]+条": ["content:law_article"]
            },
            "default_tags": ["source:test"],
            "enforcement_rules": {
                "tags": ["role:karlach"],
                "keywords": ["强制执行"]
            },
            "importance_rules": {
                "high": {"tags": ["type:persona"]},
                "medium": {"keywords": ["关卡"]}
            },
            "conflict_rules": {
                "role": 1
            }
        }
        with cls.schema_path.open('w', encoding='utf-8') as f:
            json.dump(cls.test_schema, f)
        
        cls.tagger = Tagger(cls.schema_path)

    @classmethod
    def tearDownClass(cls):
        # Clean up the dummy schema file
        if cls.schema_path.exists():
            os.remove(cls.schema_path)

    def test_path_mapping(self):
        """Test direct mapping from filename/path."""
        tags, _ = self.tagger.infer_tags("some content", "persona.txt")
        self.assertIn("role:karlach", tags)
        self.assertIn("type:persona", tags)

    def test_keyword_mapping(self):
        """Test tag inference from keywords in content."""
        tags, _ = self.tagger.infer_tags("内容包含地狱引擎", "some_file.txt")
        self.assertIn("topic:infernal_engine", tags)

    def test_regex_mapping(self):
        """Test tag inference from regular expressions."""
        tags, _ = self.tagger.infer_tags("这是第十条的内容", "law_file.txt")
        self.assertIn("content:law_article", tags)

    def test_metadata_override(self):
        """Test that tags in metadata have priority."""
        metadata = {"tags": ["manual:tag", "role:other"]}
        tags, _ = self.tagger.infer_tags("content", "persona.txt", metadata)
        self.assertIn("manual:tag", tags)
        self.assertIn("role:other", tags)
        self.assertIn("type:persona", tags) # from path mapping

    def test_tag_normalization(self):
        """Test cleaning and normalization of tags."""
        metadata = {"tags": ["  whitespace ", ["nested", "  whitespace  "], "DUPLICATE", "DUPLICATE", None]}
        tags, _ = self.tagger.infer_tags("", "f.txt", metadata)
        self.assertEqual(tags, ["duplicate", "nested", "source:test", "whitespace"])

    def test_enforcement_inference(self):
        """Test inference of metadata.enforcement."""
        # By tag
        _, meta = self.tagger.infer_tags("c", "persona.txt")
        self.assertTrue(meta.get('enforcement'))
        
        # By keyword
        _, meta = self.tagger.infer_tags("强制执行此操作", "f.txt")
        self.assertTrue(meta.get('enforcement'))

    def test_importance_inference(self):
        """Test inference of metadata.importance."""
        # High importance by tag
        _, meta = self.tagger.infer_tags("c", "persona.txt")
        self.assertEqual(meta.get('importance'), 'high')

        # Medium importance by keyword
        _, meta = self.tagger.infer_tags("这是一个关卡", "f.txt")
        self.assertEqual(meta.get('importance'), 'medium')

    def test_conflict_detection(self):
        """Test detection of conflicting tags."""
        metadata = {"tags": ["role:user1", "role:user2"]}
        _, meta = self.tagger.infer_tags("c", "f.txt", metadata)
        self.assertIn('__tag_conflict', meta)
        self.assertIn('role', meta['__tag_conflict'])
        self.assertIn('role:user1', meta['__tag_conflict']['role'])
        self.assertIn('role:user2', meta['__tag_conflict']['role'])

if __name__ == '__main__':
    unittest.main()
