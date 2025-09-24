import sys
from pathlib import Path
import json
import traceback

# Add project root to the Python path to ensure modules are found
try:
    project_root = Path(__file__).parent.resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from knowledge_base_service import VectorDatabase, Document
except ImportError:
    print("Error: Could not import VectorDatabase. Make sure this script is in the project root directory.")
    sys.exit(1)

def parse_tags(tag_string: str) -> list[str] | None:
    """Parses a comma-separated string of tags into a list."""
    if not tag_string.strip():
        return None
    return [tag.strip() for tag in tag_string.split(',')]

def main():
    """Main function for the interactive search script."""
    print("Initializing vector database...")
    try:
        db = VectorDatabase()
        if not db.documents:
            print("\nWarning: The database appears to be empty.")
            print("Please ensure you have run the import script (e.g., 'import_docs.py') first.")
    except Exception as e:
        print(f"\nError initializing database: {e}")
        print("Please ensure your environment variables (e.g., EMBEDDING_API_KEY) are set correctly.")
        traceback.print_exc()
        sys.exit(1)

    print("\n--- Interactive Vector Search ---")
    print("Type 'quit' or 'exit' at the query prompt to leave.")

    while True:
        try:
            # 1. Get search query
            query = input("\n\n[1/5] Enter your search query: ").strip()
            if query.lower() in ['quit', 'exit']:
                print("Exiting interactive search. Goodbye!")
                break
            if not query:
                print("Query cannot be empty. Please try again.")
                continue

            # 2. Get various tag types
            tags_all_str = input("[2/5] Enter AND tags (e.g., role:karlach, type:persona): ").strip()
            tags_any_str = input("[3/5] Enter OR tags (e.g., lang:en, lang:zh): ").strip()
            priority_tags_str = input("[4/5] Enter Priority tags (to boost score): ").strip()
            
            # 3. Get top_k
            top_k_str = input("[5/5] How many results to return (default: 5): ").strip()
            top_k = int(top_k_str) if top_k_str.isdigit() else 5

            # 4. Parse inputs
            tags_all = parse_tags(tags_all_str)
            tags_any = parse_tags(tags_any_str)
            priority_tags = parse_tags(priority_tags_str)

            # 5. Perform search
            print("\nSearching...")
            results = db.search(
                query=query,
                tags_all=tags_all,
                tags_any=tags_any,
                priority_tags=priority_tags,
                top_k=top_k
            )

            # 6. Display results
            if not results:
                print("\n--- No results found. ---")
            else:
                print(f"\n--- Found {len(results)} results: ---")
                for i, doc in enumerate(results, 1):
                    print(f"\n[{i}] Document ID: {doc.id}")
                    print(f"    Tags: {doc.tags}")
                    print(f"    Content: {doc.content[:200]}...") # Print a snippet
                    if doc.metadata:
                        print(f"    Metadata: {doc.metadata}")

        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting interactive search. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
