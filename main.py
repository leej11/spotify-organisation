# https://spotipy.readthedocs.io/en/2.17.1/

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import pandas as pd


def create_spotipy_authed_instance(scope: str):
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


def get_user_saved_tracks(limit: int = 20):

    #### Scopes
    # - https://developer.spotify.com/documentation/general/guides/scopes/#user-library-read
    # Create spotipy.Spotify instance
    sp = create_spotipy_authed_instance('user-library-read')

    # Call the user saved tracks method
    saved_tracks = sp.current_user_saved_tracks(limit=limit)

    songs_dict = {}

    for idx, item in enumerate(saved_tracks['items']):
        track = item['track']
        artist_name = track['artists'][0]['name']
        track_name = track['name']
        date_added = item['added_at']
        date_added = convert_added_at_to_datetime(date_added)
        id = track['id']
        uri = track['uri']

        print(idx, track_name, artist_name, id, date_added)

        songs_dict[uri] = [track_name, artist_name, id, date_added]

    songs_df = pd.DataFrame.from_dict(songs_dict, orient='index', columns=['Track Name', 'Artist Name', 'ID', 'Date Added'])

    songs_df['YearMonth Added'] = songs_df['Date Added'].dt.strftime("%Y%m")

    return songs_df


def convert_added_at_to_datetime(timestamp: str):

    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return timestamp


def create_new_playlist(
        playlist_name: str,
        public: bool = True,
        collborative: bool = False,
        description: str = '',
):
    sp = create_spotipy_authed_instance('playlist-modify-public')

    sp.user_playlist_create(
        user=sp.current_user()['id'],
        name=playlist_name,
        public=public,
        collaborative=collborative,
        description=description,
    )


def get_playlists():
    sp = create_spotipy_authed_instance('playlist-read-private')
    playlists = sp.current_user_playlists()
    playlists_dict = {}

    for idx, item in enumerate(playlists['items']):
        playlists_dict[item['name']] = item

    playlists_df = pd.DataFrame.from_dict(playlists_dict, orient='index')

    return playlists_df



#sp.user_playlist_add_tracks()

if __name__ == '__main__':

    # Get a list of all my saved tracks
    songs = get_user_saved_tracks()

    created_playlists = []

    # For each distinct YearMonth that I've saved songs in, create an associated playlist
    for yearmonth, frame in songs.groupby('YearMonth Added'):

        create_new_playlist(
            f'{yearmonth}-python-test',
            description=f'My test playlist using python for: {yearmonth}',
        )
        created_playlists.append(f'{yearmonth}-python-test')

    # Get the list of all my playlists, so I can get their IDs
    playlists = get_playlists()

    # Add the songs to the associated YearMonth playlist
    for yearmonth, frame in songs.groupby('YearMonth Added'):

        playlist = f"{yearmonth}-python-test"

        if playlist in playlists.index.values:
            print(f"Playlist {yearmonth} exists")

            sp = create_spotipy_authed_instance('playlist-modify-public')

            sp.playlist_add_items(
                playlist_id=playlists.loc[playlist]['uri'],
                items=list(frame.ID.values),
            )

    print("Completed YearMonth playlist creation")