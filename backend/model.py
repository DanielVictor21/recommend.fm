import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import OneHotEncoder
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
import random



class ArtistRecommender:
    def __init__(self, new_user_artists):
        # Load the data
        file_path = 'data/data.csv'
        self.data = pd.read_csv(file_path)
        self.artist_data = self.data.iloc[:, 1:]

        # Load the trained models
        self.encoder = joblib.load('AI-Model/encoder.joblib')
        self.svd = joblib.load('AI-Model/svd.joblib')
        self.kmeans_svd = joblib.load('AI-Model/kmeans_svd.joblib')
        self.svd_clusters = joblib.load('AI-Model/svd_clusters.joblib')
        self.new_user_artists = new_user_artists


    def recommend_artists(self, n_recommendations=5, n_top_users=10):
        # Create a dataframe with the same structure as the original artist_data
        new_user_data = pd.DataFrame([self.new_user_artists], columns=self.artist_data.columns[:len(self.new_user_artists)])

        # Fill missing columns with the most frequent artist
        most_frequent_artist = self.artist_data.mode().iloc[0]
        for col in self.artist_data.columns[len(self.new_user_artists):]:
            new_user_data[col] = most_frequent_artist[col]

        # Ensure the columns are in the same order
        new_user_data = new_user_data[self.artist_data.columns]

        # Encode the new user's artists
        encoded_new_user = self.encoder.transform(new_user_data)

        # Reduce dimensionality using the trained TruncatedSVD model
        new_user_svd = self.svd.transform(encoded_new_user)

        # Predict the cluster for the new user
        new_user_cluster = self.kmeans_svd.predict(new_user_svd)[0]

        # Get all users in the same cluster
        same_cluster_users = np.where(self.svd_clusters == new_user_cluster)[0]

        # Calculate weighted similarity scores for users in the same cluster
        weights = np.linspace(1, 0.5, num=len(self.new_user_artists))
        similarity_scores = []
        for user_idx in same_cluster_users:
            user_data = self.artist_data.iloc[user_idx].values
            common_artists = set(self.new_user_artists) & set(user_data)
            score = sum(weights[self.new_user_artists.index(artist)] for artist in common_artists if artist in self.new_user_artists)
            similarity_scores.append((user_idx, score))
        
        # Sort users by similarity scores in descending order
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Randomly sample from the top similar users
        top_similar_users = [score[0] for score in similarity_scores[:n_top_users]]
        sampled_users = random.sample(top_similar_users, min(len(top_similar_users), n_top_users))

        # Collect artists from the sampled similar users
        recommended_artists = []
        for user_idx in sampled_users:
            user_artists = self.artist_data.iloc[user_idx].values.flatten()
            for artist in user_artists:
                if artist not in self.new_user_artists and artist not in recommended_artists:
                    recommended_artists.append(artist)
                if len(recommended_artists) >= n_recommendations:
                    break
            if len(recommended_artists) >= n_recommendations:
                break

        return recommended_artists

