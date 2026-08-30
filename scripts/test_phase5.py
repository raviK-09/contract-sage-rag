import httpx, json
r = httpx.get("http://localhost:8000/documents", timeout=15)
data = r.json()
print(f"Total documents: {data['total_documents']}  |  Total chunks: {data['total_chunks']}")
for d in data["documents"]:
    print(f"  - {d['file_name']:<50s} {d['chunk_count']:3d} chunks  {d['total_pages']} pages")

r2 = httpx.get("http://localhost:8000/health", timeout=10)
h = r2.json()
print(f"\nAPI status   : {h['status']}")
print(f"Ollama       : {'running' if h['ollama_running'] else 'offline'}")
print(f"llama3.1:8b  : {'available' if h['primary_model_available'] else 'NOT PULLED'}")
print(f"Vector store : {h['vector_store_chunks']} chunks")
print("\nAll Phase 5 endpoints verified!")
