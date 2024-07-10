from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from backend.model import ArtistRecommender
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('API_KEY')

app = FastAPI()

#function to make a query to the database, and return the names and url
def get_artist_info(artists):
    uri= "mongodb://localhost:27017/" # endpoit to your mongodb, i used the pre-defined
    client = MongoClient(uri)
    results = []

    try:
        database = client['Artistas']  
        collection = database['artistas']  

        for artist in artists:
            # Check if the artist exists in the bank
            query = { artist: { "$exists": True } }
            projection = {
                f"{artist}.album_name": 1,
                f"{artist}.artist_img": 1,
                f"{artist}.url_imagem_album": 1,
                "_id": 0
            }

            result = collection.find_one(query, projection)
            if result and artist in result:
                artist_info = result[artist]
                album_name = artist_info.get("album_name", "N/A")
                artist_img = artist_info.get("artist_img", "N/A")
                url_imagem_album = artist_info.get("url_imagem_album", "N/A")
                artist_info = { #add a dictionary with the info to the empty list
                    'artist': artist,
                    'album_name': album_name,
                    'artist_img': artist_img,
                    'album_img': url_imagem_album,
                }
                results.append(artist_info)

            else:
                results.append(f"Artist: {artist} - No documents found!\n")
    finally:
        client.close()
    
    return results

#get the photo of the user
def get_photo(name): 
    url = f"https://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={name}&api_key={api_key}&format=json"
    response = requests.get(url)
    data = response.json()
    img = data['user']['image'][3]['#text']
    return img

#get user artists
def get_info(user):
    user_info_url = f"https://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={user}&api_key={api_key}&format=json"
    user_info_response = requests.get(user_info_url)
    user_info_data = user_info_response.json()

    if 'user' not in user_info_data:
        return "User not found on Last.fm"

    # Fetch weekly artist chart
    weekly_chart_url = f"https://ws.audioscrobbler.com/2.0/?method=user.getweeklyartistchart&user={user}&api_key={api_key}&format=json"
    weekly_chart_response = requests.get(weekly_chart_url)
    weekly_chart_data = weekly_chart_response.json()

    artistas_usuario = []
    try:
        for name in range(0, 30):
            artistas = weekly_chart_data['weeklyartistchart']['artist'][name]['name']
            artistas_usuario.append(artistas)
    except IndexError:
        pass

    # If weekly artist chart is empty, fetch top artists
    if not artistas_usuario:
        top_artists_url = f"https://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={user}&api_key={api_key}&format=json"
        top_artists_response = requests.get(top_artists_url)
        top_artists_data = top_artists_response.json()

        topartists = []
        try:
            for name in range(0, 30):
                artistas = top_artists_data['topartists']['artist'][name]['name']
                topartists.append(artistas)
        except IndexError:
            pass

        return topartists

    return artistas_usuario



templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/double", response_class=HTMLResponse)
async def read_double(request: Request):
    return templates.TemplateResponse("double.html", {"request": request})

@app.post("/double_recommender", response_class=HTMLResponse)
async def read_double(request: Request, user1: str = Form(...), user2: str = Form(...)):
    topartists1 = get_info(user1)
    topartists2 = get_info(user2)
    if topartists1 == "User not found on Last.fm" or topartists2 == "User not found on Last.fm":
        return templates.TemplateResponse("double.html", {"request": request, "message": "one of both doesn't have a last.fm account."})
    
    topartists = topartists1 + topartists2
    combined = []
    j = len(topartists) - len(topartists2)
    try:
        for i in range(30):
            if i < len(topartists):
                combined.append(topartists[i])
            if j >= 0 and j != i:  # Avoid duplicating the same index
                combined.append(topartists[j])
            j += 1
    except IndexError:
        pass

    # Limit combined list to 30 items
    combined = combined[:30]

    recommend = ArtistRecommender(combined)
    recommendations = recommend.recommend_artists()
    user_photo1 = get_photo(user1)
    user_photo2 = get_photo(user2)
    responses = get_artist_info(recommendations)
    return templates.TemplateResponse("double_recommender.html", {"request": request, "user1": user1, "user2": user2, "infos": responses, "photo1": user_photo1, "photo2": user_photo2})

@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.post("/send", response_class=HTMLResponse)
async def receive_form(request: Request, user: str = Form(...)):
    topartists = get_info(user)
    print(topartists)
    if topartists == "User not found on Last.fm":
        return templates.TemplateResponse("index.html", {"request": request, "message": "User not found on Last.fm"})
    else:
        recommend = ArtistRecommender(topartists)
        recommendations = recommend.recommend_artists()
        user_photo = get_photo(user)
        responses = get_artist_info(recommendations)
    return templates.TemplateResponse("recommend.html", {"request": request, "user": user, "infos": responses, "photo": user_photo})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
