import sys
import discord
from discord.ext import commands
import os
import MusicBotConfig
import requests
import git


discordIntents = discord.Intents.all()

bot = commands.Bot(command_prefix=MusicBotConfig.prefix, intents=discordIntents)

bot.remove_command("help")

global extensionName
extensionName = "MusicBot"

@bot.event
async def on_ready():
    global extensionName
    run = True
    os.system('cls' if os.name == 'nt' else 'clear')
    if (len(sys.argv) > 1):
        if (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
            print(MusicBotConfig.helpMessage)
            return
        
        elif (sys.argv[1] == "--base" or sys.argv[1] == "-b"):
            return
        
        elif (sys.argv[1] == "--file" or sys.argv[1] == "-f"):
            if (len(sys.argv) > 2):
                extensionName = sys.argv[2]
            else:
                print("Please provide a filename")
                return
                
    if (run):
        try:
            print(os.getcwd())
            await bot.load_extension(extensionName)
        except Exception as e:
            print("Error loading " + extensionName + ":")
            print(e)
            pass

@bot.command()
async def restart(ctx:commands.context, *args):
    global extensionName
    if ctx.author.id == 320837660900065291:
        try:
            print("Restart")
            os.chdir(os.path.dirname(__file__))
            print(os.getcwd())

            if (len(args) > 0):
                for arg in args:
                    print("Reload: " + arg)
                    await ctx.message.reply("Reloading: " + arg)
                    await bot.reload_extension(arg)

            elif (len(list(bot.extensions.keys())) > 0):
                loadedExtensions = list(bot.extensions.keys())
                for extension in loadedExtensions:
                    print("Reload: " + extension)
                    await ctx.message.reply("Reloading: " + extension)
                    await bot.reload_extension(extension)

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

        g = git.cmd.Git(os.path.dirname(__file__))
        g.pull()

bot.run(MusicBotConfig.token)