import discord
from discord.ext import commands, tasks
import json
from pulsefire.clients import RiotAPIClient

intents = discord.Intents.default()
intents.messages = True
intents.guild_messages = True
intents.message_content = True

discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')
    loop.start()

@tasks.loop(seconds=60)
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
                summoner = await add_user(message.content)
                await message.channel.send(f'Successfully added {summoner["name"]} to database')
            except Exception as e:
                print(f"Error: {e}")
                await message.channel.send("Error Occurred: Check Logs")
    if message.content.startswith('$commands'):
        await message.channel.send('Commands:\n Add User: Format <$add username#tag>')

async def add_user(message):
    components = message.split()
    if len(components) == 2 and '#' in components[1]:
        username, tag = components[1].split('#', 1)
    else: 
        raise ValueError("Invalid username and tag format")

    async with RiotAPIClient(default_headers={"X-Riot-Token": "RGAPI-1adbcee0-6c9d-48de-9ce0-5a58af8c7385"}) as client:
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
            "username": username,
            "tag": tag,
            "puuid": account["puuid"]
        }
        data.append(user_data)

        # Write updated data
        with open('users.json', 'w') as json_file:
            json.dump(data, json_file, indent=2)
    return summoner

discord_client.run('NzI5MzQyMTE2OTQxMDA0OTIw.G-3_Si.J3z6SF-6rjkzRVTji8-_VbG7QxzEW2IaLDAtuU')