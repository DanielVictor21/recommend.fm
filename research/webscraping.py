import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import pandas as pd
import time
import csv
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('API_KEY')

# This is the webscraping that i used to create de data.csv
artists = []
for n in range(1, 5):
    url2 = f"https://www.last.fm/charts/weekly?page={n}"
    response2 = requests.get(url2)
    
    if response2.status_code == 200:
        soup = BeautifulSoup(response2.content, "html.parser")
        artist_elements = soup.find_all('a', class_='link-block-target')
        for artist_element in artist_elements:
            artist_name = artist_element.text.strip()
            artists.append(artist_name)

elementos_para_remover = ['TURN IT UP', 'GRASA', 'Frog in Boiling Water', 'MTG - Mega das Tchutchucas 2']
for elemento in elementos_para_remover:
    while elemento in artists:
        artists.remove(elemento)

print("Artistas:", artists)

usernames = []
pessoas = {}

for name in artists:
    encoded_name = quote(name)
    url = f"https://www.last.fm/music/{encoded_name}/+listeners"
    response1 = requests.get(url)
    if response1.status_code == 200:
        soup = BeautifulSoup(response1.content, "html.parser")
        user_elements = soup.find_all(class_="link-block-target", href=True)
        for user_element in user_elements:
            if "/user/" in user_element["href"]:
                names = []
                username = user_element.text.strip()
                usernames.append(username)
                url3 = f'https://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={username}&api_key={api_key}&format=json'
                response3 = requests.get(url3)
                data = response3.json()
                try:
                    for name in range(0, 30):
                        artistas = data['topartists']['artist'][name]['name']
                        names.append(artistas)
                except IndexError:
                    continue
                except KeyError:
                    continue
                else:
                    print(username,":",names)
                    with open('data.csv', 'a', newline='', encoding='utf-8') as arquivo_csv:
                        escritor_csv = csv.writer(arquivo_csv)
                        escritor_csv.writerow([username, names[0],names[1],names[2],names[3],names[4],names[5],names[6],
                                               names[7],names[8],names[9],names[10],names[11],names[12],names[13],names[14]
                                               ,names[15],names[16],names[17],names[18],names[19],names[20],names[21],names[22]
                                               ,names[23],names[24],names[25],names[26],names[27],names[28],names[29]])
                                               