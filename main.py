# https://spotipy.readthedocs.io/en/2.17.1/
from typing import List
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import pandas as pd


def create_spotipy_authed_instance(scopes: List[str]):
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))


def get_user_saved_tracks(limit: int = 20):
    """
    Note: The docs say the maximum limit = 50.

    :param limit:
    :return:
    """

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

    sp.user_playlist_create(
        user=sp.current_user()['id'],
        name=playlist_name,
        public=public,
        collaborative=collborative,
        description=description,
    )


def get_playlists():

    playlists = sp.current_user_playlists()
    playlists_dict = {}

    for idx, item in enumerate(playlists['items']):
        playlists_dict[item['name']] = item

    playlists_df = pd.DataFrame.from_dict(playlists_dict, orient='index')

    return playlists_df



#sp.user_playlist_add_tracks()

if __name__ == '__main__':

    # Spotify Authorisation with all scopes
    sp = create_spotipy_authed_instance(
        [
            'user-library-read', # We use this to read my saved tracks library
            'playlist-read-private', # To read all my playlists I've created
            'playlist-modify-public', # To create, and modify my playlists
        ]
    )

    # Get a list of all my saved tracks
    songs = get_user_saved_tracks(49)

    created_playlists = []

    # Get the list of all my playlists before creating any new ones
    playlists = get_playlists()

    # For each distinct YearMonth that I've saved songs in, create an associated playlist
    for yearmonth, frame in songs.groupby('YearMonth Added'):

        playlist = f"{yearmonth}-python-test"

        if playlist in playlists.index.values:
            print(f"Playlist {yearmonth} already exists")

        else:
            create_new_playlist(
                playlist,
                description=f'My test playlist using python for: {yearmonth}',
            )
            created_playlists.append(f'{yearmonth}-python-test')

    # Get the list of all my playlists, so I can get their IDs
    updated_list_of_playlists = get_playlists()

    # Add the songs to the associated YearMonth playlist
    for yearmonth, frame in songs.groupby('YearMonth Added'):

        playlist = f"{yearmonth}-python-test"

        # If it's a newly created playlist, just add all the items
        if playlist in created_playlists:

            sp.playlist_add_items(
                playlist_id=playlists.loc[playlist]['uri'],
                items=list(frame.ID.values),
            )

        elif playlist in updated_list_of_playlists.index.values:

            # Read current contents of playlist
            current_playlist_details = sp.playlist_items(
                playlist_id=playlists.loc[playlist]['uri'],
            )

            current_playlist_track_ids = [
                item['track']['id'] for item in current_playlist_details['items']
            ]

            # Determine tracks not already in playlist (set diff)
            new_tracks = list(
                set(frame.ID.values).difference(current_playlist_track_ids)
            )

            if new_tracks:
                sp.playlist_add_items(
                    playlist_id=playlists.loc[playlist]['uri'],
                    items=new_tracks,
                )

            else:
                print("No new tracks to add.")

    print("Completed YearMonth playlist creation")