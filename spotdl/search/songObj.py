from spotdl.search.provider import search_and_get_best_match, get_lyrics
from spotdl.search.spotifyClient import get_spotify_client

from os.path import join

from json import dumps as convert_dict_to_json, loads as convert_json_to_dict

from typing import List

class SongObj():
    #! This can be accessed as songObj.searchProvider. songObj acts like a namespace
    #! it allows us a convenient way of setting a search provider without using globals
    searchProvider = search_and_get_best_match

    #====================
    #=== Constructors ===
    #====================
    def __init__(self, rawTrackMeta, rawAlbumMeta, rawArtistMeta, youtubeLink, lyrics):
        self. __rawTrackMeta = rawTrackMeta
        self.__rawAlbumMeta  = rawArtistMeta
        self.__rawArtistMeta = rawArtistMeta
        self.__youtubeLink   = youtubeLink
        self.__playlistIndex = None
        self.__lyrics = lyrics

    #! constructors here are a bit mucky, there are two different constructors for two
    #! different use cases, hence the actual __init__ function does not exist

    #! Note, since the following are class methods, an instance of songObj is initialized
    #! and passed to them
    @classmethod
    def from_url(cls, spotifyURL: str):
        # check if URL is a playlist, user, artist or album, if yes raise an Exception,
        # else procede
        if not (('open.spotify.com' in spotifyURL and 'track' in spotifyURL)
            or spotifyURL.startswith('spotify:track:')):
            raise Exception('passed URL is not that of a track: %s' % spotifyURL)



        # query spotify for song, artist, album details
        spotifyClient = get_spotify_client()

        rawTrackMeta = spotifyClient.track(spotifyURL)

        primaryArtistId = rawTrackMeta['artists'][0]['id']
        rawArtistMeta = spotifyClient.artist(primaryArtistId)

        albumId = rawTrackMeta['album']['id']
        rawAlbumMeta = spotifyClient.album(albumId)



        # get best match from the given provider
        songName = rawTrackMeta['name']

        albumName = rawTrackMeta['album']['name']

        duration = round(
            rawTrackMeta['duration_ms'] / 1000,
            ndigits = 3
        )

        contributingArtists = []

        for artist in rawTrackMeta['artists']:
            contributingArtists.append(artist['name'])

        youtubeLink = SongObj.searchProvider(
            songName,
            contributingArtists,
            albumName,
            duration
        )

        youtubeLink = youtubeLink

        # Get Lyrics Using Songs Name and Primary Artist's name.
        lyrics = get_lyrics(songName, contributingArtists[0])

        return  cls(
            rawTrackMeta, rawAlbumMeta,
            rawArtistMeta, youtubeLink,
            lyrics
        )

    @classmethod
    def from_dump(cls, dataDump: dict):
        rawTrackMeta  = dataDump['rawTrackMeta']
        rawAlbumMeta  = dataDump['rawAlbumMeta']
        rawArtistMeta = dataDump['rawAlbumMeta']
        youtubeLink   = dataDump['youtubeLink']
        lyrics        = dataDump['lyrics']
        playlistIndex = dataDump['playlistIndex']

        returnObj = cls(
            rawTrackMeta, rawAlbumMeta,
            rawArtistMeta, youtubeLink,
            lyrics
        )
        returnObj.set_playlist_index(playlistIndex)

        return returnObj

    def __eq__(self, comparedSong) -> bool:
        if comparedSong.get_data_dump() == self.get_data_dump():
            return True
        else:
            return False

    #================================
    #=== Interface Implementation ===
    #================================

    def set_playlist_index(self, playlistIndex):
        '''
        sets a song's track number within a playlist (as in the index of the track
        within the playlist and not the album, see get_track_number for that.)
        This can be used to prepend the number to filename to keep output files
        ordered with respect to their original order in playlist.
        Set to None to disable.
        '''
        self.__playlistIndex = playlistIndex
    
    def get_playlist_index(self) -> int:
        '''
        returns song's track number within the playlist (as in the index of the track
        within the playlist and not the album, see get_track_number for that.)
        This can be used to prepend the number to filename to keep output files
        ordered with respect to their original order in playlist.
        returns None if it wasn't set.
        '''
        return self.__playlistIndex

    def get_youtube_link(self) -> str:
        return self.__youtubeLink
    
    def get_spotify_link(self) -> str:
        return 'http://open.spotify.com/track/' + self.__rawTrackMeta['id']

    def get_spotify_link(self) -> str:
        return 'http://open.spotify.com/track/' + self.__rawTrackMeta['id']

    #! Song Details:

    #! 1. Name
    def get_song_name(self) -> str:
        ''''
        returns songs's name.
        '''

        return self.__rawTrackMeta['name']

    #! 2. Track Number
    def get_track_number(self) -> int:
        '''
        returns song's track number from album (as in weather its the first
        or second or third or fifth track in the album)
        '''

        return self.__rawTrackMeta['track_number']

    #! 3. Genres
    def get_genres(self) -> List[str]:
        '''
        returns a list of possible genres for the given song, the first member
        of the list is the most likely genre. returns None if genre data could
        not be found.
        '''

        return self.__rawAlbumMeta['genres'] + self.__rawArtistMeta['genres']

    #! 4. Duration
    def get_duration(self) -> float:
        '''
        returns duration of song in seconds.
        '''

        return round(self.__rawTrackMeta['duration_ms'] / 1000, ndigits = 3)

    #! 5. All involved artists
    def get_contributing_artists(self) -> List[str]:
        '''
        returns a list of all artists who worked on the song.
        The first member of the list is likely the main artist.
        '''

        # we get rid of artist name that are in the song title so
        # naming the song would be as easy as
        # $contributingArtists + songName.mp3, we would want to end up with
        # 'Jetta, Mastubs - I'd love to change the world (Mastubs remix).mp3'
        # as a song name, it's dumb.

        contributingArtists = []

        for artist in self.__rawTrackMeta['artists']:
            contributingArtists.append(artist['name'])

        return contributingArtists

    #! 6. Song Lyrics
    def get_song_lyrics(self) -> str:
        '''
        returns the lyrics of the song.
        '''

        return self.__lyrics

    #! Album Details:

    #! 1. Name
    def get_album_name(self) -> str:
        '''
        returns name of the album that the song belongs to.
        '''

        return self.__rawTrackMeta['album']['name']

    #! 2. All involved artist
    def get_album_artists(self) -> List[str]:
        '''
        returns list of all artists who worked on the album that
        the song belongs to. The first member of the list is likely the main
        artist.
        '''

        albumArtists = []

        for artist in self.__rawTrackMeta['album']['artists']:
            albumArtists.append(artist['name'])

        return albumArtists

    #! 3. Release Year/Date
    def get_album_release(self) -> str:
        '''
        returns date/year of album release depending on what data is available.
        '''

        return self.__rawTrackMeta['album']['release_date']

    #! Utilities for genuine use and also for metadata freaks:

    #! 1. Album Art URL
    def get_album_cover_url(self) -> str:
        '''
        returns url of the biggest album art image available.
        '''

        return self.__rawTrackMeta['album']['images'][0]['url']

    #! 2. All the details the spotify-api can provide
    def get_data_dump(self) -> dict:
        '''
        returns a dictionary containing the spotify-api responses as-is. The
        dictionary keys are as follows:
            - rawTrackMeta      spotify-api track details
            - rawAlbumMeta      spotify-api song's album details
            - rawArtistMeta     spotify-api song's artist details

        Avoid using this function, it is implemented here only for those super
        rare occasions where there is a need to look up other details. Why
        have to look it up seperately when it's already been looked up once?
        '''

        #! internally the only reason this exists is that it helps in saving to disk

        return {
            'playlistIndex'  : self.__playlistIndex,
            'youtubeLink'  : self.__youtubeLink,
            'rawTrackMeta' : self.__rawTrackMeta,
            'rawAlbumMeta' : self.__rawAlbumMeta,
            'rawArtistMeta': self.__rawArtistMeta,
            'lyrics'       : self.__lyrics
        }
