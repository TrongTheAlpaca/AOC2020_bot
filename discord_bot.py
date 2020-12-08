import os

import json

import requests
import random
from datetime import datetime, timedelta

from pathlib import Path

import discord

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# TODO LIST:
# - Create logger https://discordpy.readthedocs.io/en/latest/logging.html
# - Add playing status https://discordpy.readthedocs.io/en/latest/faq.html#how-do-i-set-the-playing-status
# - MOVE TO ENV
# - Make it so I can check downloaded history through


def update_leaderboard_json():
    print('UPDATING LEADERBOARD JSON')

    # Get Current Leaderboard JSON
    url = os.getenv('LB_JSON')
    cookies = dict(
        session=os.getenv('SES_COOKIE'))
    r = requests.get(url, cookies=cookies)

    # Save json to file
    today = datetime.now().date().isoformat()
    with open(f'history/leaderboard_{today}.json', 'w', encoding='utf-8') as f:
        json.dump(json.loads(r.text), f, ensure_ascii=False, sort_keys=True, indent=4)


def get_leaderboard_announcement():
    """
    :return:
    """
    print('GET LEADERBOARD ANNOUNCEMENT')

    yesterday = (datetime.today() - timedelta(days=1)).date().isoformat()
    today = datetime.now().date().isoformat()

    ### READ FROM JSON FILE
    with open(f'history/leaderboard_{yesterday}.json', 'r', encoding='utf-8') as f:
        json_yesterday = json.loads(f.read())['members']

    with open(f'history/leaderboard_{today}.json', 'r', encoding='utf-8') as f:
        json_today = json.loads(f.read())['members']

    ### READ FROM FILES
    with open(f'encouragement', 'r', encoding='utf-8') as f:
        encouragements_original = [line.strip('\n') for line in f.readlines()]

    leaderboard_string = "```\n"
    leaderboard_string += f"ADVENT OF CODE - UPDATE {today} 🦌🎅⛄\n"
    leaderboard_string += "******************************************\n"

    players_tba = []
    for player_id in json_today:
        # Skip if new player or skip if user doesn't have name
        if player_id in json_yesterday and json_today[player_id]['name']:
            players_tba.append(player_id)
    random.random()

    encouragements = random.sample(encouragements_original, len(players_tba))

    for ind, player_id in enumerate(players_tba):
        name = json_today[player_id]['name']
        stars_yesterday = json_yesterday[player_id]['stars']
        stars_today = json_today[player_id]['stars']

        new_stars = stars_today - stars_yesterday
        if new_stars > 0:
            leaderboard_string += f"- {name:<20} +{new_stars}⭐ (new total: {stars_today:>2}⭐)! {encouragements[ind]}\n"


    # Welcoming new players
    new_player_ids = set(json_today) - set(json_yesterday)
    if len(new_player_ids) > 0:
        leaderboard_string += f"\nWELCOME NEW MEMBERS! 👀\n"
        for new_id in new_player_ids:
            leaderboard_string += f"- {json_today[new_id]['name']}\n"

    leaderboard_string += f"\n💎Join the fun! \nhttps://adventofcode.com/ - Leaderboard Code: 665622-85fb1ee8\n```"

    print(leaderboard_string)
    return leaderboard_string


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.announce_leaderboard,
                               CronTrigger(hour=12,
                                           minute=0,
                                           end_date='2021-01-02',
                                           timezone='Europe/Oslo')
                               )
        self.scheduler.start()

    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == '!history':
            print("Message from: ", message.author)
            print("Read message from channel: ", message.channel)

            x = ''.join(['- ' + str(file)+'\n' for file in Path('history').iterdir()])

            await message.channel.send(f'```Stored History\n{x}```')

        if message.content == '!update':
            print("Message from: ", message.author)
            print("Read message from channel: ", message.channel)

            update_leaderboard_json()

            await message.channel.send(f'UPDATED!')

            x = ''.join(['- ' + str(file) + '\n' for file in Path('history').iterdir()])

            await message.channel.send(f'```Stored History\n{x}```')

        if message.content == '!ping':
            print("Message from: ", message.author)
            print("Read message from channel: ", message.channel)
            await message.channel.send('pong')

    @staticmethod
    async def announce_leaderboard():
        update_leaderboard_json()
        announcement_string = get_leaderboard_announcement()
        channel = client.get_channel(int(os.getenv('CH_GENERAL')))
        await channel.send(announcement_string)


client = MyClient()
client.run(os.getenv('DC_TOKEN'))
