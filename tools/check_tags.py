import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Union
from collections import Counter

# Add project root to sys.path to allow importing from the root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Now that the path is set, we can import the service
from knowledge_base_service import VectorDatabase as KnowledgeBaseService

def normalize_tags(tags_list: list) -> Tuple[List[str], bool]:
    """
    Normalizes a list of tags: flattens, removes whitespace, duplicates, non-string elements,
    and converts to lowercase.
    Returns the cleaned list and a boolean indicating if changes were made.
    """
    if not isinstance(tags_list, list):
        original_repr = repr(tags_list)
        tags_list = [str(tags_list)]
        was_changed = True
    else:
        original_repr = repr(tags_list)
        was_changed = False

    flat_tags = []
    
    def flatten(items):
        nonlocal was_changed
        for item in items:
            if isinstance(item, list):
                was_changed = True
                flatten(item)
            elif item is not None:
                # Convert to string, remove full-width spaces, strip, and lowercase
                cleaned_tag = str(item).replace('　', ' ').strip().lower()
                if cleaned_tag:
                    flat_tags.append(cleaned_tag)
            else:
                was_changed = True # Found a None value

    flatten(tags_list)
    
    # Remove duplicates while preserving order (for comparison)
    seen = set()
    unique_tags = [x for x in flat_tags if not (x in seen or seen.add(x))]
    
    final_repr = repr(unique_tags)

    # More robust change detection
    if not was_changed and original_repr != final_repr:
        was_changed = True

    return unique_tags, was_changed

def main():
    parser = argparse.ArgumentParser(description="Check and fix tags in the knowledge base.")
    parser.add_argument('--report', action='store_true', help='Generate a JSON report of tag issues.')
    parser.add_argument('--apply', action='store_true', help='Apply fixes for found issues.')
    parser.add_argument('--file', type=str, help='Path to the documents.json file to check.')
    parser.add_argument('--schema', type=str, help='Path to the tag_schema.json file.')
    args = parser.parse_args()

    documents_path: Path
    schema_path: Path
    kb_service: KnowledgeBaseService

    if args.file:
        documents_path = Path(args.file).resolve()
        # Pass the custom file path to the service as well
        # The service expects the directory, not the file itself
        db_dir = documents_path.parent
        kb_service = KnowledgeBaseService(data_dir=str(db_dir))
    else:
        # Default path relative to the script's location
        documents_path = Path(project_root) / 'data' / 'documents.json'
        kb_service = KnowledgeBaseService()

    if args.schema:
        schema_path = Path(args.schema).resolve()
    else:
        schema_path = Path(project_root) / 'configs' / 'tag_schema.json'

    # Load the tag schema
    try:
        with schema_path.open('r', encoding='utf-8') as f:
            tag_schema: Dict[str, Dict[str, Any]] = json.load(f)
        valid_namespaces = set(tag_schema.keys())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading tag schema from {schema_path}: {e}")
        sys.exit(1)


    # The kb_service now holds the single source of truth for documents and tags for the given file.
    issues: List[Dict[str, Any]] = []
    issues_found = 0
    fixed_count = 0
    
    # Use the kb_service that was initialized correctly
    all_tags_from_index = set(kb_service.tag_index.keys())
    docs_from_service = list(kb_service.documents.values())

    # Check 1 & 3 & 4 & 5: Iterate through documents for various issues
    all_doc_tags = set()
    for doc in docs_from_service:
        doc_id = doc.id
        doc_tags_raw = doc.tags
        
        # Ensure doc_tags is a list of strings, filtering out malformed data
        doc_tags = {tag for tag in doc_tags_raw if isinstance(tag, str)}
        all_doc_tags.update(doc_tags)

        # Check for issues based on the schema
        tag_namespaces: Dict[str, List[str]] = {}
        for tag in doc_tags:
            if ':' in tag:
                namespace, value = tag.split(':', 1)
                
                # Check 1: Unrecognized namespace
                if namespace not in valid_namespaces:
                    issues.append({
                        'doc_id': doc_id,
                        'type': 'unrecognized_namespace',
                        'details': f"Tag '{tag}' has an unrecognized namespace '{namespace}'.",
                        'fix': 'remove_tag'
                    })
                    issues_found += 1
                    continue # Skip other checks for this tag

                # Check for enum validation if schema specifies it
                if "enum" in tag_schema[namespace] and value not in tag_schema[namespace]["enum"]:
                    issues.append({
                        'doc_id': doc_id,
                        'type': 'invalid_tag_value',
                        'details': f"Tag '{tag}' has value '{value}' which is not in the allowed enum for namespace '{namespace}'.",
                        'fix': 'manual_review_required'
                    })
                    issues_found += 1

                if namespace not in tag_namespaces:
                    tag_namespaces[namespace] = []
                tag_namespaces[namespace].append(tag)
            else:
                # Tag does not follow namespace:value format
                issues.append({
                    'doc_id': doc_id,
                    'type': 'malformed_tag',
                    'details': f"Tag '{tag}' does not follow the 'namespace:value' format.",
                    'fix': 'remove_tag'
                })
                issues_found += 1
        
        # Check 3: Namespace conflict
        for namespace, tags in tag_namespaces.items():
            # Only check for conflict if the schema specifies single_choice
            if tag_schema.get(namespace, {}).get("type") == "single_choice" and len(tags) > 1:
                issues.append({
                    'doc_id': doc_id,
                    'type': 'namespace_conflict',
                    'details': f"Multiple tags for single_choice namespace '{namespace}': {tags}",
                    'fix': 'manual_review_required'
                })
                issues_found += 1

    # Check 2: Find tags in the index that are not in any document (dangling tags)
    dangling_tags = all_tags_from_index - all_doc_tags
    for tag in dangling_tags:
        issue = {
            'doc_id': None,
            'type': 'missing_tag_from_documents',
            'details': f"Tag '{tag}' exists in index but not in any document.",
            'fix': 'remove_from_index' # This is a conceptual fix
        }
        issues.append(issue)
        issues_found += 1
    
    # This structure is simplified; a full implementation would need to handle all issue types.
    report_data = {
        "report_generated": datetime.now().isoformat(),
        "documents_file": str(documents_path),
        "total_documents": len(docs_from_service),
        "total_tags_in_index": len(all_tags_from_index),
        "issues_found": issues_found,
        "issues": issues
    }

    if args.report:
        print(json.dumps(report_data, indent=4, ensure_ascii=False))

    elif args.apply and issues:
        print(f"\nApplying fixes for {issues_found} issues...")
        
        # Create a backup by renaming the original file
        backup_file = documents_path.with_name(f"{documents_path.name}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        documents_path.rename(backup_file)
        print(f"Backup created at: {backup_file}")

        # Apply fixes to the in-memory list of documents
        docs_to_write = [d.model_dump() for d in docs_from_service]
        
        for issue in issues:
            if issue.get('fix') == 'remove_tag':
                doc_id_to_fix = issue['doc_id']
                
                # Determine the tag to remove from the details string
                details = issue['details']
                if "Tag '" in details:
                    tag_to_remove = details.split("'")[1]
                else:
                    continue # Cannot determine tag to remove

                # Find the document in our list to modify
                doc_to_modify = next((d for d in docs_to_write if d['id'] == doc_id_to_fix), None)
                
                if doc_to_modify and 'tags' in doc_to_modify and tag_to_remove in doc_to_modify['tags']:
                    doc_to_modify['tags'].remove(tag_to_remove)
                    fixed_count += 1

        # Write the modified documents back to the original file path
        with documents_path.open('w', encoding='utf-8') as f:
            json.dump(docs_to_write, f, indent=4, ensure_ascii=False)
        
        print(f"Applied {fixed_count} fixes to {documents_path.name}.")

    else:
        if not args.report:
            print("No action specified. Use --report to see issues or --apply to fix them.")
            if issues:
                print(f"Found {issues_found} potential issues.")
            else:
                print("No issues found.")

def run():
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    run()
