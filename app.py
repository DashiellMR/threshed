import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import asyncio
import requests
import httpx
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

server_url = "http://localhost:5000"
#TODO: implement specific recent check // IN-PROGRESS
#      make the recent matches prettier // IN-PROGRESS
#      add average placement to recent games // NOT-STARTED
#      add current rank to recent games // NOT-STARTED
#      finish implementing stats menu // IN-PROGRESS
#      conversion from json to sqlite // IN-PROGRESS
#      implementation of flask backend // IN-PROGRESS

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='add')
async def add(ctx, args):
    username, tag = args.split('#', 1)
    account_data = {"discord_account": ctx.author.name,
                    "username": username, 
                    "tag": tag}
    
    # Send a POST request to Flask app
    response = requests.post(f'{server_url}/add', json=account_data)

    # Check response
    if response.status_code == 200:
        await ctx.send(f"Successfully added user: {username}#{tag}")
    else:
        await ctx.send(f"Failed to add user: {response.text}")

@bot.command(name='remove')
async def remove(ctx, args):
    username, tag = args.split('#', 1)
    account_data = {"discord_account": ctx.author.name,
                    "username": username, 
                    "tag": tag}
    response = requests.post(f'{server_url}/remove', json=account_data)
    if response.status_code == 200:
        await ctx.send(f"Successfully removed user: {username}#{tag}")
    else:
        await ctx.send(f"Failed to add user: {response.text}")

@bot.command(name='recent')
async def recent(ctx, args):
    username, tag = args.split('#', 1)
    account_data = {"discord_account": ctx.author.name,
                    "username": username, 
                    "tag": tag}
    response = requests.post(f'{server_url}/recent', json=account_data)
    if response.status_code == 200:
        await ctx.send(f"Here are your recent 10 games: {response.text}")
    else: 
        await ctx.send("Failed to retrieve match data, please check if your username and/or tag were inputted properly.")

@bot.command(name='get')
async def stats(ctx, args):
    data = {"RIOT_KEY": args}
    req = requests.post(f"{server_url}/add", json=data)
    await ctx.send(req.json()["RIOT_KEY"])

@bot.command(name='list')
async def list(ctx):
    req = requests.get(f"{server_url}/list")
    data = req.text
    await ctx.send("Current User List:")
    output = ""
    #for item in data:
        #output+=(f"{item["username"]}#{item["tag"]}\n")
    await ctx.send(data)

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send("pong")

bot.run(f"{DISCORD_KEY}")