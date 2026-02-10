import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def cluster_by_similarity(items, vectors, threshold=0.86):
    clusters = []
    centroids = []

    for i, v in enumerate(vectors):
        if not clusters:
            clusters.append([i]); centroids.append(v); continue

        sims = cosine_similarity([v], centroids)[0]
        j = int(np.argmax(sims))

        if sims[j] >= threshold:
            clusters[j].append(i)
            centroids[j] = np.mean([vectors[k] for k in clusters[j]], axis=0)
        else:
            clusters.append([i]); centroids.append(v)

    return clusters