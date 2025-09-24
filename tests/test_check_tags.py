import unittest
from pathlib import Path
import sys
import os
import json
from datetime import datetime

# Add project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# The script to be tested is a command-line tool, so we'll use subprocess
import subprocess

class TestCheckTags(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for the class."""
        cls.script_path = Path(__file__).parent.parent / 'tools' / 'check_tags.py'
        cls.test_data_dir = Path(__file__).parent / 'test_data_cleanup'
        cls.test_data_dir.mkdir(exist_ok=True)
        cls.test_docs_path = cls.test_data_dir / 'documents.json'
        cls.test_schema_path = cls.test_data_dir / 'tag_schema.json'
        
        # This is the canonical source for test data
        cls.original_test_documents = [
            {"id": "doc1", "content": "Test content 1", "tags": ["role:user", "unrecognized:tag"]}, # unrecognized namespace
            {"id": "doc2", "content": "Test content 2", "tags": ["status:draft", "status:published"]}, # single_choice conflict
            {"id": "doc3", "content": "Test content 3", "tags": ["role:invalid_role"]}, # invalid enum value
            {"id": "doc4", "content": "Test content 4", "tags": ["not-a-namespaced-tag"]}, # malformed tag
        ]

        # This is the schema for testing
        cls.test_schema = {
            "role": {
                "type": "single_choice",
                "enum": ["user", "admin", "editor"]
            },
            "status": {
                "type": "single_choice",
                "enum": ["draft", "published", "archived"]
            }
        }

    def setUp(self):
        """Set up clean test files before each test."""
        # Write a fresh copy of the documents for each test
        with open(self.test_docs_path, 'w', encoding='utf-8') as f:
            json.dump(self.original_test_documents, f, indent=4)
        # Write a fresh copy of the schema for each test
        with open(self.test_schema_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_schema, f, indent=4)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment once after all tests are run."""
        if cls.test_docs_path.exists():
            os.remove(cls.test_docs_path)
        if cls.test_schema_path.exists():
            os.remove(cls.test_schema_path)
        
        # Clean up backup files
        for backup_file in cls.test_data_dir.glob("*.bak.*"):
            os.remove(backup_file)
        
        if cls.test_data_dir.exists():
            try:
                os.rmdir(cls.test_data_dir)
            except OSError:
                # Directory might not be empty if other files were created
                pass

    def run_script(self, *args):
        """Helper to run the check_tags.py script."""
        script_path = project_root / 'tools' / 'check_tags.py'
        
        cmd = [sys.executable, str(script_path), '--file', str(self.test_docs_path)] + list(args)
        result = subprocess.run(cmd, capture_output=True)
        return result

    def test_report_mode(self):
        """Test the --report functionality."""
        # Run the script with --report
        result = subprocess.run(
            [sys.executable, str(self.script_path), '--report', 
             '--file', str(self.test_docs_path),
             '--schema', str(self.test_schema_path)],
            capture_output=True
        )

        stdout_decoded = result.stdout.decode('utf-8', errors='replace')
        stderr_decoded = result.stderr.decode('utf-8', errors='replace')

        self.assertEqual(result.returncode, 0, f"Script failed with output:\nSTDOUT:\n{stdout_decoded}\nSTDERR:\n{stderr_decoded}")

        # Verify the JSON output
        try:
            report_data = json.loads(stdout_decoded)
        except json.JSONDecodeError:
            self.fail(f"Script did not produce valid JSON output. STDOUT:\n{stdout_decoded}")

        self.assertEqual(report_data['issues_found'], 4, "Incorrect number of issues found in report.")

    def test_apply_mode(self):
        """Test the --apply functionality."""
        # Run the script with --apply
        result = subprocess.run(
            [sys.executable, str(self.script_path), '--apply',
             '--file', str(self.test_docs_path),
             '--schema', str(self.test_schema_path)],
            capture_output=True
        )

        stdout_decoded = result.stdout.decode('utf-8', errors='replace')
        stderr_decoded = result.stderr.decode('utf-8', errors='replace')
        
        self.assertEqual(result.returncode, 0, f"Script failed with output:\nSTDOUT:\n{stdout_decoded}\nSTDERR:\n{stderr_decoded}")

        # Verify that the file was modified correctly
        with open(self.test_docs_path, 'r', encoding='utf-8') as f:
            docs_after = json.load(f)
        
        doc1_after = next((d for d in docs_after if d['id'] == 'doc1'), None)
        self.assertIsNotNone(doc1_after, "doc1 should still exist after apply.")
        # 'unrecognized:tag' and 'not-a-namespaced-tag' should be removed
        self.assertNotIn('unrecognized:tag', doc1_after.get('tags', []), "Unrecognized namespace tag was not removed.")
        self.assertIn('role:user', doc1_after.get('tags', []), "Correct tag was accidentally removed.")

        doc4_after = next((d for d in docs_after if d['id'] == 'doc4'), None)
        self.assertIsNotNone(doc4_after, "doc4 should still exist after apply.")
        self.assertEqual(doc4_after.get('tags', []), [], "Malformed tag should have been removed.")

if __name__ == '__main__':
    unittest.main()
