import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from dotenv import load_dotenv
from pulsefire.clients import RiotAPIClient
from pulsefire.schemas import RiotAPISchema
from pulsefire.taskgroups import TaskGroup

load_dotenv()

RIOT_KEY = os.getenv('RIOT_KEY')
DISCORD_KEY = os.getenv('DISCORD_KEY')

intents = discord.Intents.default()
intents.messages = True
intents.guild_messages = True
intents.message_content = True

discord_client = discord.Client(intents=intents)


#TODO: implement specific recent  check
#      implement removal from json file
#      make the recent matches prettier
#      add average placement to recent games
#      add current rank to recent games
#      


@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')
    loop.start()

@tasks.loop(seconds=5)
async def loop():
    try:
        cur_channel = discord_client.get_channel(1190789769865723954)  # Use an integer for the channel ID
        if cur_channel:
            print(f"Channel Acquired: {cur_channel}")
            with open("users.json") as f:
                data = json.load(f)
            for item in data:
                print(item["username"], item["puuid"])
        else:
            print("Channel not found.")
    except Exception as e:
        print(f"Error: {e}")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return
    if message.content.startswith('$add'):
            try:
                print("Attempt Received")
                summoner = await add_user(message.content, message.author.name)
                await message.channel.send(f'Successfully added {summoner["name"]} to database')
            except Exception as e:
                print(f"Error: {e}")
                await message.channel.send("Error Occurred: Check Logs")
    if message.content.startswith('$commands'):
        await message.channel.send('Commands:\n Add User: Format <$add username#tag>')
    if message.content.startswith('$recent'):
        try:
            print("Attempting to grab recent games") 
            output = await recent_games(message.content, message.author.name) 
            await message.channel.send(output)
        except Exception as e:
           print(f"Error: {e}")

async def add_user(message, author):
    components = message.split()
    if len(components) == 2 and '#' in components[1]:
        username, tag = components[1].split('#', 1)
    else: 
        raise ValueError("Invalid username and tag format")

    async with RiotAPIClient(default_headers={"X-Riot-Token": f"{RIOT_KEY}"}) as client:
        account = await client.get_account_v1_by_riot_id(region="americas", game_name=username, tag_line=tag)
        if account is None:
            raise ValueError("Account not found")
        # Check if account is a dictionary and has 'puuid'
        if not isinstance(account, dict) or "puuid" not in account:
            raise TypeError("Unexpected response format from get_account_v1_by_riot_id")
        summoner = await client.get_tft_summoner_v1_by_puuid(region="na1", puuid=account["puuid"])
        # Read existing data
        try:
            with open('users.json', 'r') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []
        # Check for duplicate
        if any(user['username'] == username and user['tag'] == tag for user in data):
            raise ValueError("User already exists")
        # Append new data
        user_data = {
            "discord_account": author,
            "username": username,
            "tag": tag,
            "puuid": account["puuid"]
        }
        data.append(user_data)
        # Write updated data
        with open('users.json', 'w') as json_file:
            json.dump(data, json_file, indent=2)
    return summoner
async def recent_games(message, author):
    with open("users.json") as f:
        data = json.load(f)
        cur_puuid = next((item["puuid"] for item in data if item["discord_account"] == author), None)

    if cur_puuid is None:
        return "User not found."

    async with RiotAPIClient(default_headers={"X-Riot-Token": f"{RIOT_KEY}"}) as client:
        if message == "$recent":
            match_ids = await client.get_tft_match_v1_match_ids_by_puuid(region="americas", puuid=cur_puuid)
            placements = []
            async with TaskGroup(asyncio.Semaphore(100)) as tg: 
                for match_id in match_ids[:20]:
                    await tg.create_task(client.get_tft_match_v1_match(region="americas", id=match_id)) 
            matches = tg.results() 

            for match in matches:
                # Find the participant with the current puuid
                for participant in match['info']['participants']:
                    if participant['puuid'] == cur_puuid:
                        placements.append(participant['placement'])
                        break  # Break the loop once the participant is found

        return placements

discord_client.run(f"{DISCORD_KEY}")