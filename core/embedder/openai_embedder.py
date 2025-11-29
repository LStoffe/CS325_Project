
import os
from openai import OpenAI

class OpenAIEmbedder:
    def __init__(self, logger):
        api_key=os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment.")
        self.client=OpenAI(api_key=api_key)
        self.log=logger

    def embed_batch(self, texts):
        self.log("[Embedding] Creating embeddings...")
        resp=self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [d.embedding for d in resp.data]
