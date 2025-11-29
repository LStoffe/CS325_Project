from openai import OpenAI
import numpy as np

class OpenAIEmbedder:
    """
    Embeds text using OpenAI's embedding models.
    Produces numpy arrays for direct cosine similarity.
    """

    def __init__(self, model="text-embedding-3-small"):
        self.client = OpenAI()
        self.model = model

    def embed_batch(self, texts):
        # Ensure valid strings
        texts = [str(t) for t in texts]

        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        # Return embeddings as numpy arrays
        return [np.array(item.embedding) for item in response.data]
