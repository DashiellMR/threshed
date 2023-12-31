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

client = RiotAPIClient(default_headers={"X-Riot-Token": f"{RIOT_KEY}"})
intents = discord.Intents.default()
intents.messages = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

#TODO: implement specific recent check // IN-PROGRESS
#      implement removal from json file // DONE
#      make the recent matches prettier // IN-PROGRESS
#      add average placement to recent games // NOT-STARTED
#      add current rank to recent games // NOT-STARTED
#      implement discord.ext bot commands // DONE
#      finish implementing stats menu // IN-PROGRESS

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='add')
async def add(ctx, args):
    username, tag = args.split('#', 1)
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
            "discord_account": ctx.author.name,
            "username": username,
            "tag": tag,
            "puuid": account["puuid"]
        }
        data.append(user_data)
        # Write updated data
        with open('users.json', 'w') as json_file:
            json.dump(data, json_file, indent=2)
    await ctx.send(f"Successfully added user: {username}#{tag}")
    return summoner

@bot.command(name='remove')
async def remove(ctx, args):
    username, tag = args.split('#', 1)
    with open("users.json", 'r') as f:
        data = json.load(f)

    removed = False
    for item in data:
        if item["discord_account"] == ctx.author.name and item["username"]==username and item["tag"]==tag:
            data.remove(item)
            removed = True
            break
    if removed:
        with open("users.json", 'w') as f:
            json.dump(data, f)
        await ctx.send(f"Succesfully removed {username}#{tag} from the database.")
    else:
        await ctx.send("You do not have permission to delete that user or the user does not exist.")

@bot.command(name='recent')
async def recent(ctx):
        found = False
        with open("users.json", 'r') as f: 
            data = json.load(f)
        for item in data:
            if item["discord_account"]==ctx.author.name:
                puuid = item["puuid"]
                found = True
                break
        if found:
            placements = []
            async with RiotAPIClient(default_headers={"X-Riot-Token": f"{RIOT_KEY}"}) as client:
                match_ids = await client.get_tft_match_v1_match_ids_by_puuid(region="americas", puuid=puuid)
                async with TaskGroup(asyncio.Semaphore(100)) as tg: 
                    for match_id in match_ids[:20]:
                        await tg.create_task(client.get_tft_match_v1_match(region="americas", id=match_id)) 
                matches = tg.results() 
            for match in matches:
                # Find the participant with the current puuid
                for participant in match['info']['participants']:
                    if participant['puuid'] == puuid:
                        placements.append(participant['placement'])
                        break  # Break the loop once the participant is found
            await ctx.send(f"Here are your 20 most recent games: {placements}")
@bot.command(name='stats')
async def stats(ctx, args=None):
    if (args != None):
        args = ctx.author.name


@bot.command(name='ping')
async def ping(ctx):
    await ctx.send("pong")

bot.run(f"{DISCORD_KEY}")