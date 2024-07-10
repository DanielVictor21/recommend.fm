import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
import joblib

data = pd.read_csv('data/data.csv')

# Taking away the usernames
artist_data = data.iloc[:, 1:]

# enconding categorial data
encoder = OneHotEncoder(handle_unknown='ignore')
encoded_artists = encoder.fit_transform(artist_data)

svd = TruncatedSVD(n_components=50, random_state=42)
artist_data_svd = svd.fit_transform(encoded_artists)

kmeans_svd = KMeans(n_clusters=5, random_state=42)
kmeans_svd.fit(artist_data_svd)
# after some tests, the n_cluster=5 was with the best silhouette avg.

svd_clusters = kmeans_svd.predict(artist_data_svd)

svd_silhouette_avg = silhouette_score(artist_data_svd, svd_clusters)
svd_silhouette_avg

joblib.dump(encoder, 'encoder.joblib')
joblib.dump(svd, 'svd.joblib')
joblib.dump(kmeans_svd, 'kmeans_svd.joblib')
joblib.dump(svd_clusters, 'svd_clusters.joblib')
# transfer the model to joblib

def recommend_artists(new_user_artists):
    # Create a dataframe with the same structure as the original artist_data
    new_user_data = pd.DataFrame([new_user_artists], columns=artist_data.columns[:len(new_user_artists)])

    # Fill missing columns with the most frequent artist
    most_frequent_artist = artist_data.mode().iloc[0]
    for col in artist_data.columns:
        if col not in new_user_data:
            new_user_data[col] = most_frequent_artist[col]

    # Ensure the columns are in the same order
    new_user_data = new_user_data[artist_data.columns]

    # Encode the new user's artists
    encoded_new_user = encoder.transform(new_user_data)

    # Reduce dimensionality using the trained TruncatedSVD model
    new_user_svd = svd.transform(encoded_new_user)

    # Predict the cluster for the new user
    new_user_cluster = kmeans_svd.predict(new_user_svd)[0]

    # Get all users in the same cluster
    same_cluster_users = np.where(svd_clusters == new_user_cluster)[0]

    # Calculate weighted similarity scores for users in the same cluster
    weights = np.linspace(1, 0.5, num=len(new_user_artists))
    similarity_scores = []
    for user_idx in same_cluster_users:
        user_data = artist_data.iloc[user_idx].values
        common_artists = set(new_user_artists) & set(user_data)
        score = sum(weights[new_user_artists.index(artist)] for artist in common_artists if artist in new_user_artists)
        similarity_scores.append((user_idx, score))
    
    # Sort users by similarity scores in descending order
    similarity_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Collect artists from the top similar users
    recommended_artists = []
    for user_idx, _ in similarity_scores:
        user_artists = artist_data.iloc[user_idx].values.flatten()
        for artist in user_artists:
            if artist not in new_user_artists and artist not in recommended_artists:
                recommended_artists.append(artist)
            if len(recommended_artists) >= 5:
                break
        if len(recommended_artists) >= 5:
            break

    return recommended_artists