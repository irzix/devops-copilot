import uuid
import chromadb
from typing import List, Tuple

# Initialize ChromaDB persistent client pointing to data volume
# Will resolve to /app/data/chroma_db inside Docker containers
client = chromadb.PersistentClient(path="data/chroma_db")

# Fetch or create the security guardrail collection
collection = client.get_or_create_collection(name="security_blacklist")

async def init_and_seed_db():
    """
    Checks if the security blacklist collection has documents.
    If empty, populates it with default dangerous command templates and reasons.
    """
    if collection.count() == 0:
        default_seeds = [
            {
                "pattern": "rm -rf /",
                "reason": "Recursive deletion of the root directory. Results in absolute OS loss."
            },
            {
                "pattern": "rm -rf /etc",
                "reason": "Recursive deletion of configuration directories. Breaks system configuration."
            },
            {
                "pattern": "mkfs.ext4 /dev/sda",
                "reason": "Formatting raw storage drive. Destroys filesystem structure and partition data."
            },
            {
                "pattern": "dd if=/dev/zero of=/dev/sda",
                "reason": "Zero-writing raw block device. Wipes partition tables and master boot records."
            },
            {
                "pattern": "iptables -F",
                "reason": "Flushing active firewall rules. Exposes the server to external connection attempts."
            },
            {
                "pattern": "cat /etc/shadow",
                "reason": "Exposing system shadow user file. Leaks hashed credentials database."
            },
            {
                "pattern": "chmod 777 -R /",
                "reason": "Recursive permissive access modifier. Allows unprivileged write and execution globally."
            },
            {
                "pattern": "reboot",
                "reason": "Forces hard system restart. Terminates running containers and processes instantly."
            },
            {
                "pattern": "shutdown -h now",
                "reason": "Forces host system shutdown. Takes the server offline."
            }
        ]

        ids = [f"seed_{i}" for i in range(len(default_seeds))]
        documents = [item["pattern"] for item in default_seeds]
        metadatas = [{"reason": item["reason"]} for item in default_seeds]

        # Sync add to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

def is_command_safe(command: str) -> Tuple[bool, str, float]:
    """
    Performs semantic similarity check of proposed shell command against blacklist.
    Returns (is_safe, reason, similarity_score).
    """
    # Fetch closest match (n_results=1)
    results = collection.query(
        query_texts=[command],
        n_results=1
    )

    if results and results["documents"] and len(results["documents"][0]) > 0:
        matched_doc = results["documents"][0][0]
        distance = results["distances"][0][0]  # L2 distance metric
        metadata = results["metadatas"][0][0]

        # Convert L2 distance to Cosine Similarity score: 1.0 - (L2 / 2.0)
        # ChromaDB ONNX embeddings are L2-normalized, making this conversion mathematically valid.
        similarity = 1.0 - (distance / 2.0)

        # Flag commands with a similarity index higher than 0.75 (L2 distance < 0.5)
        if similarity > 0.75:
            return (
                False,
                f"Blocked: Command matches dangerous pattern '{matched_doc}'. Reason: {metadata['reason']}",
                similarity
            )

        return True, "No critical security threats detected.", similarity

    return True, "Guardrail threat database is empty.", 0.0

def add_blacklist_pattern(pattern: str, reason: str) -> dict:
    """Adds a new custom forbidden pattern to the ChromaDB vector database."""
    pattern_id = f"custom_{uuid.uuid4().hex}"
    collection.add(
        ids=[pattern_id],
        documents=[pattern],
        metadatas=[{"reason": reason}]
    )
    return {"id": pattern_id, "pattern": pattern, "reason": reason}

def get_all_blacklist_patterns() -> List[dict]:
    """Retrieves all registered dangerous patterns inside the RAG collection."""
    results = collection.get()
    patterns = []
    if results and "ids" in results:
        for i in range(len(results["ids"])):
            patterns.append({
                "id": results["ids"][i],
                "pattern": results["documents"][i],
                "reason": results["metadatas"][i]["reason"]
            })
    return patterns
