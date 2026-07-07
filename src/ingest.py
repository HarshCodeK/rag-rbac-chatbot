import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL, CHROMA_DB_PATH, DATA_DIR, COLLECTIONS


def chunk_text(text: str, chunk_size: int = 300) -> list[str]:
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > chunk_size and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def build_all_collections():
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    model = SentenceTransformer(EMBEDDING_MODEL)

    for collection_name in COLLECTIONS:
        folder = os.path.join(DATA_DIR, collection_name)
        txt_files = glob.glob(os.path.join(folder, "*.txt"))
        all_chunks = []
        for filepath in txt_files:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            all_chunks.extend(chunk_text(text))

        if not all_chunks:
            print(f"{collection_name}: 0 chunks")
            continue

        collection = client.get_or_create_collection(name=collection_name)
        embeddings = model.encode(all_chunks).tolist()
        ids = [f"{collection_name}_{i}" for i in range(len(all_chunks))]
        metadatas = [{"source": collection_name} for _ in all_chunks]

        if collection.count() > 0:
            collection.delete(ids=collection.get()["ids"])
        collection.add(
            documents=all_chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        print(f"{collection_name}: {len(all_chunks)} chunks stored")
