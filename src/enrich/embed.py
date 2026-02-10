from openai import OpenAI
import numpy as np

client = OpenAI()

def embed_texts(texts, model: str):
    resp = client.embeddings.create(model=model, input=texts)
    return [np.array(d.embedding, dtype=np.float32) for d in resp.data]