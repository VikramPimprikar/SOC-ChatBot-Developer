from pinecone import Pinecone
import uuid

class VectorService:
    def __init__(self, api_key: str, index_name: str):
        pc = Pinecone(api_key=api_key)
        self.index = pc.Index(index_name)

    def upsert_document(self, embedding: list, document: dict):
        """
        document must ONLY contain primitive metadata values
        """

        vector_id = document.get("id", str(uuid.uuid4()))

        metadata = {
            "content": document["content"],
            "doc_id": document["doc_id"],
            "incident_type": document["incident_type"],
            "section": document["section"]
        }

        self.index.upsert(
            vectors=[(vector_id, embedding, metadata)]
        )
