import sys
import discord
from discord.ext import commands
import os
import MusicBotConfig
import requests
import git
import subprocess


discordIntents = discord.Intents.all()

bot = commands.Bot(command_prefix=MusicBotConfig.prefix, intents=discordIntents)

bot.remove_command("help")

@bot.event
async def on_ready():
    run = True
    os.system('cls' if os.name == 'nt' else 'clear')
    if (len(sys.argv) > 1):
        if (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
            print(MusicBotConfig.helpMessage)
            return
        
        elif (sys.argv[1] == "--base" or sys.argv[1] == "-b"):
            run = False
                
    if (run):
        cogDir = str(os.path.dirname(__file__) + '/Cogs').replace('/', os.path.sep)
        if (os.path.exists(cogDir)):
            for filename in os.listdir(cogDir):
                if filename.endswith('.py'):
                    print(filename)
                    await bot.load_extension(f'Cogs.{filename[:-3]}')

@bot.command()
async def restart(ctx:commands.context, *args):
    global extensionName
    if ctx.author.id == 320837660900065291:
        try:
            print("Restart")
            os.chdir(os.path.dirname(__file__))
            print(os.getcwd())

            for voice_client in bot.voice_clients:
                await voice_client.disconnect()

            if (len(args) > 0):
                for arg in args:
                    print("Reload: " + arg)
                    await ctx.message.reply("Reloading: " + arg)
                    await bot.reload_extension(arg)

            elif (len(list(bot.extensions.keys())) > 0):
                loadedExtensions = list(bot.extensions.keys())
                for extension in loadedExtensions:
                    print("Unload: " + extension)
                    await ctx.message.reply("Unloading: " + extension)
                    await bot.unload_extension(extension)
                cogDir = str(os.path.dirname(__file__) + '/Cogs').replace('/', os.path.sep)
                if (os.path.exists(cogDir)):
                    for filename in os.listdir(cogDir):
                        if filename.endswith('.py'):
                            print("Load: Cogs." + filename[:-3])
                            await ctx.message.reply("Loading: Cogs." + filename[:-3])
                            await bot.load_extension(f'Cogs.{filename[:-3]}')

            else:
                print("Load: " + extensionName)
                await ctx.message.reply("Loading: " + extensionName)
                await bot.load_extension(extensionName)
                
        except Exception as e:
            await ctx.message.reply("An error occured")
            await ctx.message.reply(e)
            print(e)
            pass

@bot.command()
async def update(ctx:commands.context):
    global extensionName
    if ctx.author.id == 320837660900065291:
        print("Update")
        
        os.chdir(os.path.dirname(__file__))
        subprocess.call(["git", "pull"])

bot.run(MusicBotConfig.token)