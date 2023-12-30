import discord
from riotwatcher import LolWatcher, ApiError

riot = LolWatcher('RGAPI-1adbcee0-6c9d-48de-9ce0-5a58af8c7385', default_status_v4=True)
region = 'na1'
id = riot.summoner.by_account(region, 'Dashiell#123')

intents = discord.Intents.default()
intents.messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('Tell me how I did!'):
        ranked_stats = riot.league.by_summoner(region, id['id'])
        await message.channel.send(f'You are currently {ranked_stats}')

client.run('NzI5MzQyMTE2OTQxMDA0OTIw.G-3_Si.J3z6SF-6rjkzRVTji8-_VbG7QxzEW2IaLDAtuU')