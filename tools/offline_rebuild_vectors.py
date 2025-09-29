from knowledge_base_service import VectorDatabase

if __name__ == "__main__":
    db = VectorDatabase()
    ok = db.rebuild_all_vectors()
    print({"success": ok})
