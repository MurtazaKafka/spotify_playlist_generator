CLIENT_ID = "y5066a8d0e1384a8ca4a587ff115c2ea8"
CLIENT_SECRET = "72d544244a6f4b7bbf7dd085e6d3c096"
REDIRECT_URI = "http://localhost:5000/callback" 

import spotipy
from spotipy.oauth2 import SpotifyOAuth


from flask import Flask, request, render_template, redirect, url_for, session
app = Flask(__name__) 
app.secret_key = "some_random_string" 

SCOPE = "user-library-read user-top-read playlist-modify-public"
MOOD_MIN = 0.0 
MOOD_MAX = 1.0 
NUM_ARTISTS = 10 
NUM_TRACKS = 20 
PLAYLIST_NAME = "Moodtape" 


def create_spotify_object():
    auth_manager = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify

def get_user_artists(spotify):
    user_artists = []
    results = spotify.current_user_top_artists(limit=NUM_ARTISTS, time_range="medium_term")
    for item in results["items"]:
        user_artists.append(item["id"]) 
    return user_artists

def get_mood_tracks(spotify, user_artists, mood):
    mood_tracks = []
    for artist in user_artists:
        results = spotify.artist_top_tracks(artist)
        for track in results["tracks"]:
            features = spotify.audio_features(track["id"])[0]
            mood_score = (features["valence"] + features["energy"]) / 2
            tolerance = 0.1
            if abs(mood_score - mood) <= tolerance:
                mood_tracks.append(track["id"])
    return mood_tracks

def create_playlist(spotify, mood_tracks):
    user_id = spotify.current_user()["id"] 
    playlist = spotify.user_playlist_create(user_id, PLAYLIST_NAME)
    playlist_id = playlist["id"] 
    spotify.user_playlist_add_tracks(user_id, playlist_id, mood_tracks) 
    return playlist

@app.route("/")
def index():
    return render_template("index.html") 

@app.route("/login")
def login():
    spotify = create_spotify_object()
    auth_url = spotify.oauth2.get_authorize_url() 
    return redirect(auth_url) 

@app.route("/callback")
def callback():
    spotify = create_spotify_object()
    code = request.args.get("code")
    token_info = spotify.oauth2.get_access_token(code) 
    session["token_info"] = token_info 
    return redirect(url_for("mood")) 

@app.route("/mood", methods=["GET", "POST"])
def mood():
    if request.method == "GET":
        return render_template("mood.html")
    else:
        mood = float(request.form.get("mood"))
        if mood < MOOD_MIN or mood > MOOD_MAX:
            return render_template("mood.html", error="Please enter a valid mood between 0.0 and 1.0")
        else:
            session["mood"] = mood
            return redirect(url_for("playlist"))

@app.route("/playlist")
def playlist():
    token_info = session.get("token_info")
    mood = session.get("mood")
    if token_info and mood:
        spotify = spotipy.Spotify(auth=token_info["access_token"])
        user_artists = get_user_artists(spotify)
        mood_tracks = get_mood_tracks(spotify, user_artists, mood)
        playlist = create_playlist(spotify, mood_tracks)
        return render_template("playlist.html", playlist=playlist)
    else:
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
