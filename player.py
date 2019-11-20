import requests
import json
from prettytable import PrettyTable

from generalutils import timeit

class AuthenticationError(Exception):
    """
    Thrown when a query requires authentication but the user is not logged in
    """
    pass

class Level(object):
    """
    Represents a level in the Runemetrics API
    """
    LEVEL_XP = [
    0,
    83,
    174,
    276,
    388,
    512,
    650,
    801,
    969,
    1154,
    1358,
    1584,
    1833,
    2107,
    2411,
    2746,
    3115,
    3523,
    3973,
    4470,
    5018,
    5624,
    6291,
    7028,
    7842,
    8740,
    9730,
    10824,
    12031,
    13363,
    14833,
    16456,
    18247,
    20224,
    22406,
    24815,
    27473,
    30408,
    33648,
    37224,
    41171,
    45529,
    50339,
    55649,
    61512,
    67983,
    75127,
    83014,
    91721,
    101333,
    111945,
    123660,
    136594,
    150872,
    166636,
    184040,
    203254,
    224466,
    247886,
    273742,
    302288,
    333804,
    368599,
    407015,
    449428,
    496254,
    547953,
    605032,
    668051,
    737627,
    814445,
    899257,
    992895,
    1096278,
    1210421,
    1336443,
    1475581,
    1629200,
    1798808,
    1986068,
    2192818,
    2421087,
    2673114,
    2951373,
    3258594,
    3597792,
    3972294,
    4385776,
    4842295,
    5346332,
    5902831,
    6517253,
    7195629,
    7944614,
    8771558,
    9684577,
    10692629,
    11805606,
    13034431,
    ]
    LEVEL_NAMES = [
    'Attack',
    'Defence',
    'Strength',
    'Constitution',
    'Ranged',
    'Prayer',
    'Magic',
    'Cooking',
    'Woodcutting',
    'Fletching',
    'Fishing',
    'Firemaking',
    'Crafting',
    'Smithing',
    'Mining',
    'Herblore',
    'Agility',
    'Thieving',
    'Slayer',
    'Farming',
    'Runecrafting',
    'Hunter',
    'Construction',
    'Summoning',
    'Dungeoneering',
    'Divination',
    'Invention',
    ]

    def __init__(self, obj):
        self.level_id = obj['id']
        self.level = obj['level']
        self.experience = int(obj['xp'] / 10)
        self.history = self.fetch_history
        self.name = self.LEVEL_NAMES[self.level_id]
        self.rates = self.fetch_rates


    def fetch_rates(self, target=99):
        """
        Gets rates for appropiate skill and filters out obsolete rates
        """
        with open('rates.json', 'r') as f:
            rates = json.load(f).get(self.name)

        res = [r for r in rates if (self.level <= r['end_range']) 
                and (range(r['start_range'],target))]

        return res

    def fetch_history(self):
        """
        Gets 12 month history of appropiate skill.

        Side notes:
        not sure about how I wanne store the overall monthly data.
        as a parameter, class attribute or
        as a file(highly doubt as file, but its convenient for now)
        """
        with open('monthly_data.json') as f:
            monthly_data = json.load(f)

        for data in monthly_data:
            for d in data.get('monthlyXpGain'):
                if d['skillId'] == self.level_id:
                    return d

    def hours_to_target(self, detailed=False, target=99):
        """
        Returns hours to target based on Exp rates in file "runemetrics/rates.json"
        """
        hours = 0
        experience = self.experience
        rates = self.fetch_rates(target=target)

        for segment in rates:
            segment['xp_req'] = self.level_experience(segment['end_range']) - experience
            segment['hours'] = segment['xp_req'] / segment['xp/hr']
            hours += segment['hours']
            experience = self.level_experience(segment['end_range'])

        if detailed:
            table = PrettyTable(['Segment','Method','XP req','hours'])
            for segment in rates:
                table.add_row([
                    '{0} -> {1}'.format(segment['start_range'],segment['end_range']),
                    segment['method'],
                    segment['xp_req'],
                    round(segment['hours'],2)
                    ])
                print(table)

        return hours

    @classmethod
    def level_experience(cls, level):
        """
        Gets the minimum required XP for a given level
        """
        return cls.LEVEL_XP[level - 1]

    @property
    def experience_to_next_level(self, target=None):
        """
        Gets the XP required to reach the next level
        """
        return self.level_experience(self.level + 1) - self.experience

class Player(object):
    """
    Represents a player in the Runemetrics API
    """
    LOGIN_URL = 'https://secure.runescape.com/m=weblogin/login.ws'
    PROFILE_URL = 'https://apps.runescape.com/runemetrics/profile/profile'
    QUEST_URL = 'https://apps.runescape.com/runemetrics/quests'

    def __init__(self, session, obj):
        self.session = session

        self.combat_level = obj['combatlevel']
        self.name = obj['name']
        self.quests_complete = obj['questscomplete']
        self.quests_started = obj['questsstarted']
        self.quests_not_started = obj['questsnotstarted']
        self.rank = int(obj['rank'].replace(',', ''))
        self.total_skill = obj['totalskill']
        self.total_experience = obj['totalxp'] / 10
        self.alog = [log for log in obj['activities']]

        levels = [Level(l) for l in obj['skillvalues']]
        self.levels = {l.name: l for l in levels}

        self.history = self.fetch_history

        if 'playtimedays' in obj:
            self.play_time = obj['playtimedays'] + obj['playtimehours'] / 24


    @classmethod
    def fetch(cls, player_name=None, session=None):
        if not session:
            session = requests.Session()
        params = {}
        if player_name:
            params['user'] = player_name
        data = session.get(
                cls.PROFILE_URL,
                params=params,
                ).json()

        if data.get('error') == 'PROFILE_PRIVATE':
            raise AuthenticationError(
                    'Player profile is private. Authenticate and try again.'
                    )
        return cls(session, data)

    @timeit
    def fetch_history(self, session=None):
        url = 'https://apps.runescape.com/runemetrics/xp-monthly'
        res = []
        if not session:
            session = requests.Session()
        for skill in self.levels:
            params = {
                    'searchName':self.name,
                    'skillid':self.levels[skill].level_id
                    }
            data = session.get(
                    url,
                    params=params,
                    ).json()
            res.append(data.get)
            print('fetching player history {:.1%}...\r'.format(len(res)/len(self.levels)),end='')
        return res


class Quests(object):
    QUEST_URL = 'https://apps.runescape.com/runemetrics/quests'

    def __init__(self, session, obj):
        self.session = session
        quests = [quest for quest in obj if not ('(' in quest['title'].title())]

        self.not_started = [quest for quest in quests if (quest['status'] == 'NOT_STARTED')]
        self.completed = [quest for quest in quests if (quest['status'] == 'COMPLETED')]
        self.started = [quest for quest in quests if (quest['status'] == 'STARTED')]

    @classmethod
    def fetch(cls, player_name=None, session=None):
        if not session:
            session = requests.Session()
        params = {}
        if player_name:
            params['user'] = player_name
        data = session.get(
                cls.QUEST_URL,
                params=params,
                ).json()
        if data.get('error') == 'PROFILE_PRIVATE':
            raise AuthenticationError(
                    'Player profile is private. Authenticate and try again.'
                    )
        return cls(session, data.get('quests'))

    def eligible(self, player_name):
        res = []
        player = Player.fetch(player_name)
        stats = player.levels

        with open('quest_data.json') as f:
            quest_data = json.load(f)

        for quest in self.not_started:
            skill_reqs = quest_data.get(quest['title'].title())['skills']
            quest_reqs = quest_data.get(quest['title'].title())['quests']
            
            check_skill_reqs = self.check_skill_reqs(stats=stats,reqs=skill_reqs)
            check_quest_reqs = self.check_quest_reqs(reqs=quest_reqs)

            if check_skill_reqs and check_quest_reqs:
                res.append(quest)

        return res

    def check_quest_reqs(self, reqs):
        if reqs is not None:
            for quest in reqs:
                for q in self.completed:
                    if q['title'].title() == quest.title():
                        pass
                    else:
                        return False
            return True
        else:
            return True

    def check_skill_reqs(self, stats, reqs):
        if reqs is not None:
            for lvl, skill in reqs:
                if lvl > stats.get(skill.title()).level:
                    return False
            return True
        else:
            return True
