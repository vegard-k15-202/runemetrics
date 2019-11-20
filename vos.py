import requests
from urllib.request import urlopen
import json
from datetime import datetime, time, date
from bs4 import BeautifulSoup

class Vos(object):
    URL = 'https://mobile.twitter.com/jagexclock'
    DISTRICTS = [
    'Amlodd',
    'Cadarn',
    'Crwys',
    'Hefin',
    'Iorwerth',
    'Ithell',
    'Meilyr',
    'Trahaearn',
    ]

    def __init__(self, obj):
        pass

    @classmethod
    def fetch(cls, player_name=None, session=None):
        """
        Retrives the most recent tweet from twitter.com/jagexclock
        """
        with urlopen(cls.URL) as req:
            html = BeautifulSoup(
                    req,
                    'lxml'
                    )
        tweets = html.find_all('table', attrs={'class':'tweet'})

        return tweets[0].find('div', attrs={'dir-ltr'}).text


