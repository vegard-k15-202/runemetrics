import json

with open('quest_dummy_data.json') as fp:
    quest_data = json.load(fp)

with open('quest_links.json') as fp:
    quest_links = json.load(fp)


for quest in quest_data['quests']:
    links = quest_links.get(quest['title'])
    if links is None:
        print(quest['title'])
