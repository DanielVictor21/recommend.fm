import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import quote, quote_plus
import json
import time
from requests.exceptions import ConnectionError, Timeout, HTTPError

df = pd.read_csv('data/data.csv')

# Throw away the usernames
df = df.iloc[:, 1:]
df
df.info()

all_artists = pd.concat([df[coluna] for coluna in df.columns]).unique()

print(len(all_artists))

def add_json(artista, url_artista, url_album, album_name, file_path ='Artistas.json'):
    try:
        # Try to open and load the existing JSON data
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty/invalid, initialize an empty dictionary
        data = {}

    data[artista] = {
        "album_name": album_name,
        "artist_img": url_artista,
        "url_imagem_album": url_album,
    }
    
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def fetch_url_with_retries(url, retries=5, backoff_factor=0.3, timeout=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except (ConnectionError, Timeout) as e:
            print(f"Error trying to get the URL: {e}. Trying again... ({attempt+1}/{retries})")
            time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff
        except HTTPError as e:
            if e.response.status_code == 404:
                print(f"Erro 404: for {url}. Skippping.")
                pass
            else:
                print(f"HTTP error: {e}. Trying again... ({attempt+1}/{retries})")
                time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff
    print(f"Failed to get the url after {retries} retries: {url}")
    return None

file_path = 'data/Artistas.json'


try:
    with open(file_path, 'r', encoding='utf-8') as file:
        existing_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    existing_data = {}


try:
    for artist in all_artists:
        if artist in existing_data:
            print(f"Artista {artist} já processado. Pulando...")
            continue
        encoded_artist = quote_plus(artist)
        url = f"https://www.last.fm/music/{encoded_artist}/+images"
        print(f"Tentando acessar a URL: {url}")
        response = fetch_url_with_retries(url)
        if response is None:
            continue
        soup = BeautifulSoup(response.content, "html.parser")
        artist_img = soup.find('li', class_='image-list-item-wrapper')
        if artist_img and artist_img.img:
            artist_img = artist_img.img['src']
        else:
            artist_img = "No image found"


        url2 = f"https://www.last.fm/music/{encoded_artist}/+albums"
        print(f"Tentando acessar a URL: {url2}")
        response2 = fetch_url_with_retries(url2)
        if response is None:
            continue
        soup = BeautifulSoup(response2.content, "html.parser")
        album_img = soup.find('span', class_='resource-list--release-list-item-image cover-art')
        if album_img and album_img.img:
            album_img = album_img.img['src']
        else:
            album_img = "No image found"
        album_name = soup.find('a', class_='link-block-target')
        if album_name:
            album_name = album_name.text
        else:
            album_name = "No album name found"
        add_json(artist, artist_img, album_img, album_name)
except Exception as e:
    print(f"Failed to get the info, {e}")
    pass

print(all_artists[-1])
#check if the last artist is the same that in the url
    