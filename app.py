from flask import Flask,render_template, redirect, request, jsonify, session, url_for

import requests

import urllib.parse

from datetime import datetime 
#youtube imports
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
app = Flask(__name__)

app.secret_key = 'asa232131423ssdadsa342423sda25534423dsadd'

#This three values are taken from the dashboard api
CLIENT_ID = '353623af0e7145529c7358dd4df726f5'
CLIENT_SECRET = '5520beef760f42bd83b44c3c6adefd26'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

all_playlists = []  # Initialize an empty list to store playlists

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():

    #https://developer.spotify.com/documentation/web-api/tutorials/implicit-flow
    # Spotify API scopes that the application is requesting access to
    scope = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative'

    #Parameters required for the authorization URL
    params = {
        'client_id' : CLIENT_ID, # Spotify client ID , it defined above
        'response_type' : 'code',  # 'code' is typically used for Authorization Code Flow "An authorization code that can be exchanged for an access token."
        'scope' : scope,        #The requested scopes for user authorization
        'redirect_uri' : REDIRECT_URI, ## Redirect URI where Spotify will redirect the user after authorization
        'show_dialog' : True  #by default this is false , but for debugging pourposes  we set it to true so we must relogin every time we refresh the page
    }

    # we need to make a get request to an authorization  url , pasiing the parameters withit 
    # Construct the authorization URL with the specified parameters
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    # Redirect the user to the Spotify authorization URL
    return redirect(auth_url)

# this defined below will be the callback that spotify will redirect after the user has loggued
# it has 2 scenarios , the user logued succesfully  or not

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    # if the  login action was succefull , they will give us back a code parameter  in that code there is a string 
    #and we need to send that string back in another request  to get the acces token
    # we prepare a dictioanry containing the necesary information to get the acces token
    if 'code' in request.args:
        req_body = {
            'code' : request.args['code'],
            'grant_type' : 'authorization_code',
            'redirect_uri' : REDIRECT_URI,
            'client_id' : CLIENT_ID,
            'client_secret' : CLIENT_SECRET
        }

        # and we send this information to the spotify token endpoint 'TOKEN URL'
        response =  requests.post(TOKEN_URL, data=req_body)

        #~if everything works well, spotify will give us the token info in a json object (something similar to a dictionary )
        #The access token is used to make requests to the Spotify API, and the refresh token can be used to obtain a new access token when the current one expires

        #https://developer.spotify.com/documentation/web-api/tutorials/code-flow
        token_info = response.json()
        #The code extracts relevant information from the JSON response and stores it in the Flask session.
        # we are going to work with three keys values that are this:
        #we use this token to make requests to spotify page
        session['access_token'] = token_info['access_token']
        # what we are going to use to refresh the previous token, because it will expire in 24 hour ("3600" that we get in expires_in)
        session['refresh_token'] = token_info['refresh_token']
        # the time that  it will take to expire the 'acces tokenkñ'
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in'] 

        return redirect('/playlist')
    
@app.route('/playlist')
def get_playlist():
    if 'access_token' not in session: #in case of error , restart
        return redirect('/login')
    

    #We check that the token is still available 
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    #Now we are good to go
    # HTTP request to the Spotify API.
    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }
    #this is the API request to the api endpoint (API_BASE_URL) including what we need and the authorization token
    #https://api.spotify.com/v1/users/{user_id}/playlists

    #all_playlists = []  # Initialize an empty list to store playlists
    n = 1

    while True: #True sera seteado por que el break se programo en linea 116
        response = requests.get(API_BASE_URL + f'me/playlists?limit=1&offset={n}', headers=headers)
        # We store the json object en un objeto python dictionary
        
          
        playlists = response.json()
         
        # Check if playlists is None or empty
        if not playlists or 'items' not in playlists:
        # Break out of the loop if there are no more playlists
            break
       
        
        # Add the playlists and his songs from the current response to the list
        for playlist in playlists['items']:
            songs = []
            response = requests.get(API_BASE_URL + f'playlists/{playlist["id"]}/tracks', headers=headers)

            canciones = response.json()
            z = 0
            for cancion in canciones['items']:
                #print(canciones['items'][z]['track']['name'])
                songname = canciones['items'][z]['track']['name']
                artists = []
                for artist_info in canciones['items'][z]['track']['artists']:
                    artist_name = artist_info['name']
                    #print('artist:',artist_name)
                    artist_info = {
                        'name': artist_name,
                    }
                    artists.append(artist_info)
                
                z = z + 1
                songs_info = {
                    'z' : z,
                    'songname' : songname,
                    'artist' : artists
                }
                songs.append(songs_info)

            playlist_info = {
            'n': n,
            'name': playlist.get('name', 'N/A'),
            'id': playlist['id'],
            'songs': songs,
            }
            all_playlists.append(playlist_info)

            response = requests.get(API_BASE_URL + f'playlists/{playlist["id"]}/tracks', headers=headers)

            canciones = response.json()
        
        n = n + 1
  
    print('all_playlist', all_playlists)
    
    return redirect('/start_query')






@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in  session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id' : CLIENT_ID,
            'client_secret' : CLIENT_SECRET
        }

    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()

    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/playlist')

def authenticate():
    print("Fetching New Tokens...")
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes=["https://www.googleapis.com/auth/youtube"]
    )
    
    # We can see this webpage on the credentials it is 'http://localhost/8080'
    flow.run_local_server(port=8080, prompt='consent')

    credentials = flow.credentials

    print(credentials.to_json())

    with open("token.pickle", "wb") as f:
        print("Saving credentials for Future Use...")
        pickle.dump(credentials, f)

    return credentials

def create_playlist(youtube, title, description):
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "privacyStatus": "public"  # You can set privacyStatus to "private" if needed
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    playlist = youtube.playlists().insert(
        part="snippet,status",
        body=request_body
    ).execute()

    return playlist['id']

def add_videos_to_playlist(youtube, playlist_id, video_ids):
    for video_id in video_ids:
        try:
            request_body = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }

            youtube.playlistItems().insert(
                part="snippet",
                body=request_body
            ).execute()

        except Exception as e:
            print(f"Error adding video {video_id} to the playlist: {e}")


# token.pickle stores the user's credentials from previously successful logins
if os.path.exists("token.pickle") and os.path.getsize("token.pickle") > 0:
    print("Loading Credentials From File...")
    with open("token.pickle", "rb") as token:
        credentials = pickle.load(token)

    # if there are no valid credentials available, or if refresh fails
    if not credentials or not credentials.valid:
        try:
            if credentials and credentials.expired and credentials.refresh_token:
                print("Refreshing Access Token...", credentials.refresh(Request()))
            else:
                raise ValueError("Invalid or expired credentials. Initiating re-authentication.")
        except Exception as e:
            print(f"Error refreshing access token: {e}")
            credentials = None

        # If refresh failed, initiate re-authentication
        if not credentials:
            credentials = authenticate()

else:
    # If no stored credentials, initiate authentication
    credentials = authenticate()


youtube = build("youtube", "v3", credentials=credentials)

@app.route('/start_query')
    # Build the YouTube API service
def start_query():
    for playlist in all_playlists:
        # Create a playlist
        playlist_title = playlist['name']
        playlist_description = playlist['name']
        #playlist_id = create_playlist(youtube, playlist_title, playlist_description)
        video_list = []
        for song in playlist['songs']:
            artist_list = []
            #print('song:',song)
            for artist in song['artist']:
                artist_name = artist['name']
                artist_list.append(artist_name)
                #print('artist:',artist_name)

            search_query = f"{song['songname']} {' '.join(artist_list)}"
            print('query:',search_query)

            search_response = youtube.search().list(
            q=search_query,
            part="id,snippet",
            type="video",
            maxResults=1  # Adjust the number of results as needed
            ).execute()
            for search_result in search_response.get("items", []):
                video_title = search_result["snippet"]["title"]
                video_id = search_result["id"]["videoId"]
                print(f"Title: {video_title}, Video ID: {video_id}")
                video_list.append(video_id)
            print('video_list = ', video_list  )
        
            
        # Create a playlist
        playlist_title = playlist['name']
        playlist_description = playlist['name']
        playlist_id = create_playlist(youtube, playlist_title, playlist_description)

        # Add videos to the playlist
        add_videos_to_playlist(youtube, playlist_id, video_list)

        print(f"Playlist '{playlist_title}' created and videos added successfully.")
    
    
    return  jsonify("succes")


 
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

 