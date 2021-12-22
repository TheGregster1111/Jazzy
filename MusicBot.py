import discord
import discord.member
import discord.channel
import discord.message
import discord.voice_client
from discord.ext import commands, tasks
import os
import MusicBotConfig
import requests
import time
import importlib

try:
    discordIntents = discord.Intents.all()

    bot = commands.Bot(command_prefix=MusicBotConfig.prefix, intents=discordIntents)

    bot.remove_command('help')

    @bot.event
    async def on_ready():
        try:
            bot.load_extension('MusicBot')
        except Exception as e:
            print(e)
            pass
    
    @bot.command()
    async def update(ctx):
        if ctx.author.id == 320837660900065291:

            try:
                if os.getcwd() == '/home/pi/MusicBot/Playlists':
                    os.chdir("..")

                try:
                    os.chdir('/home/pi/MusciBot')
                except:
                    pass

                print(os.getcwd())
                print('Unload')
                bot.unload_extension('MusicBot')
            except:
                pass

            r = requests.get('https://raw.githubusercontent.com/TheGregster1111/Jazzy/main/MusicBot.py')

            try:
                os.chdir('/home/pi/MusciBot')
            except:
                pass

            file = open('MusicBot.py', 'w')

            file.write(r.text)
            file.close()

            try:
                try:
                    os.chdir('/home/pi/MusciBot')
                except:
                    pass

                print(os.getcwd())
                bot.load_extension('MusicBot')
            except Exception as e:
                print(e)
                pass

    bot.run(MusicBotConfig.token)
    
except Exception as e:
    print('Error: {}'.format(e))
    pass
