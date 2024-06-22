import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_KEY = os.getenv('DISCORD_KEY')

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

    response = requests.post(f'{server_url}/add', json=account_data)

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
    data = response.json()
    average = sum(data)
    average=average * .1
    if response.status_code == 200:
        await ctx.send(f"Here are your recent 10 games: {response.text}\nYour average placement was {round(average, 4)}.")
    else: 
        await ctx.send("Failed to retrieve match data, please check if your username and/or tag were inputted properly.")

@bot.command(name='list')
async def list(ctx):
    req = requests.get(f"{server_url}/list")
    data = req.json()
    output = 'Current User List:\n'
    for items in data:
        output+=f"{items}\n"
    await ctx.send(output)

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send("pong")

bot.run(f"{DISCORD_KEY}")