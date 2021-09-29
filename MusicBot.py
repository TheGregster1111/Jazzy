import sys

import discord
from discord.ext.commands import bot

import discord.member

import discord.channel

import discord.message

import discord.voice_client

from discord.ext import commands, tasks
import discord_components
from discord_components import Button, ButtonStyle

import os

import MusicBotConfig

import urllib.request

from urllib.parse import urlencode, urlparse, urlunparse

import re

import pafy

import datetime

import spotipy

from spotipy import SpotifyClientCredentials

print('Test file successfully run')

class MainCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.playFromList.start()

        for filename in os.listdir(os.path.dirname(__file__) + 'Music_Cogs'):

            if filename.endswith('.py'):

                self.bot.load_extension(f'Music_Cogs.{filename[:-3]}')

        os.chdir('Playlists')

    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(MusicBotConfig.client_id, MusicBotConfig.client_secret))

    video_ids = {}
    
    skips = {}

    queue = {}

    looping = {}

    ffmpegPCM_options = {

        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 1000",

        'options': '-vn'

    }



    def spotify_to_youtube(self, playlistURL):

        results = self.spotify.playlist(playlist_id=playlistURL)



        trackList = []



        for i in results["tracks"]["items"]:



            if (i["track"]["artists"].__len__() == 1):



                trackList.append(i["track"]["name"] + " - " + i["track"]["artists"][0]["name"])



            else:

                nameString = ""



                for index, b in enumerate(i["track"]["artists"]):

                    nameString += (b["name"])



                    if (i["track"]["artists"].__len__() - 1 != index):

                        nameString += ", "



                trackList.append(i["track"]["name"] + " - " + nameString)



        return trackList



    def stop_playing(self, server):

        if self.looping.get(server.id):

            if self.looping[server.id] is False:

                del(self.video_ids[server.id][0])



                if len(self.video_ids[server.id]) == 0:

                    del(self.video_ids[server.id])

        else:

            del(self.video_ids[server.id][0])



            if len(self.video_ids[server.id]) == 0:

                del(self.video_ids[server.id])



        try:

            server.voice_client.stop()

        except:

            if server.voice_client:

                print('Something went wrong after the song stopped playing at {}'.format(datetime.datetime.now()))

    

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        if after.channel is not None:

            if after.channel.name == "Create VC":

                if after.channel.category is None:

                    await after.channel.guild.create_voice_channel("Temp VC", user_limit = after.channel.user_limit)

                    vc = after.channel.guild.voice_channels[len(after.channel.guild.voice_channels) - 1]

                    await member.move_to(vc)

                else:

                    await after.channel.category.create_voice_channel("Temp VC", user_limit = after.channel.user_limit)

                    vc = after.channel.category.voice_channels[len(after.channel.category.voice_channels) - 1]

                    await member.move_to(vc)



        if before.channel is not None:

            if self.bot.get_channel(before.channel.id).members == [] and before.channel.name == "Temp VC":

                await before.channel.delete()



        if before.channel and not member.id is self.bot.user.id and before.channel.guild.voice_client:

            if before.channel == before.channel.guild.voice_client.channel:

                if len(before.channel.members) == 1:

                    await before.channel.guild.voice_client.disconnect()



                    if self.queue.get(before.channel.guild.id):

                        del(self.queue[before.channel.guild.id])

                    if self.video_ids.get(before.channel.guild.id):

                        del(self.video_ids[before.channel.guild.id])

                    if self.looping.get(before.channel.guild.id):

                        del(self.looping[before.channel.guild.id])



    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        os.mkdir(str(guild.id), 'w')



    @commands.Cog.listener()
    async def on_guild_remove(self, guild):

        os.mkdir(str(guild.id), 'w')



    @tasks.loop(seconds=5)
    async def playFromList(self):

        for i in self.bot.voice_clients:

            if not i.is_playing() and self.video_ids.get(i.guild.id):



                song = pafy.new(self.video_ids[i.guild.id][0])



                try:

                    del(self.queue[i.guild.id][0])



                    if len(self.queue[i.guild.id]) == 0:

                        del(self.queue[i.guild.id])

                except:

                    pass



                audio = song.getbestaudio()

                i.guild.voice_client.play(discord.FFmpegPCMAudio(audio.url, **self.ffmpegPCM_options), after=lambda e: self.stop_playing(i.guild))



    @commands.command()
    async def help(self, ctx):

        embedVar = discord.Embed(title="Commands", color=0x0e41b5)

        embedVar.add_field(name='!play !p', value='Play the audio of a youtube song, playlist, or spotify playlist', inline=False)

        embedVar.add_field(name='!skip !s', value='Skip current song', inline=False)

        embedVar.add_field(name='!fs !fskip !fastskip !forceskip', value='Instantly skip current song, only useable by someone with a role named DJ or an admin', inline=False)

        embedVar.add_field(name='!queue !q', value='View the current self.queue', inline=False)

        embedVar.add_field(name='!remove !r', value='Remove the specified song from the self.queue, example: !remove 2', inline=False)

        embedVar.add_field(name='!reset', value='Reset the bot if it is malfunctioning', inline=False)

        embedVar.add_field(name='!pause', value='Pause the song', inline=False)

        embedVar.add_field(name='!continue !resume', value='Resume the song', inline=False)

        embedVar.add_field(name='!loop', value='Starts or stops self.looping the song', inline=False)

        embedVar.add_field(name='Extra stuff', value='Try making a new voice channel named "Create VC" and connecting to it', inline=False)

        await ctx.send(
            content = None,
            embed = embedVar,
            components=[
            [
            Button(
                label = "Website",
                style = ButtonStyle.URL,
                url = 'http://gamebothosting.unaux.com/'
            ),
            Button(
                label = "Discord",
                style = ButtonStyle.grey,
                url = 'https://discord.gg/qpP4CZABJx'
            ),
            Button(
                label = "Invite",
                style = ButtonStyle.grey,
                url = 'https://discord.com/api/oauth2/authorize?client_id=887684182975840296&permissions=0&scope=bot'
            )
            ]
            ]
        )



    @commands.command()
    async def reset(self, ctx):



        if not len(ctx.channel.guild.voice_client.channel.members) - 1 <= 2:

            for i in ctx.author.roles:

                    if i.name.lower() == 'dj':

                        if not ctx.author.guild_permissions.administrator:

                            return



        try:

            ctx.channel.guild.voice_client.stop()

        except:

            pass

        try:

            del(self.queue[ctx.channel.guild.id])

        except:

            pass

        try:

            del(self.video_ids[ctx.channel.guild.id])

        except:

            pass



    @commands.command()
    async def guilds(self, ctx):
        if ctx.author.id == 320837660900065291:
            message = ''
            for i in self.bot.guilds:
                message += i.name + '\n'

            await ctx.send(message)


    @commands.command()
    async def debug(self, ctx):

        if ctx.author.id == 320837660900065291:



            try:

                embedVar = discord.Embed(title="Visible self.queue", color=0x0e41b5)

                embedVar.description = ''

                for video in self.queue.get(ctx.channel.guild.id):

                    embedVar.description += video.replace('+', ' ') + '\n'

                await ctx.send(embed=embedVar)

            except:

                pass



            try:

                embedVar = discord.Embed(title="Hidden self.queue", color=0x0e41b5)

                embedVar.description = ''

                for video in self.video_ids.get(ctx.channel.guild.id):

                    embedVar.description += video.replace('+', ' ') + '\n'

                await ctx.send(embed=embedVar)

            except:

                pass



            try:

                if self.looping.get(ctx.channel.guild.id):

                    await ctx.send('Looping: {}'.format(self.looping[ctx.channel.guild.id]))

                else:

                    await ctx.send('Looping: False')

            except:

                pass



            try:

                if ctx.channel.guild.voice_client:

                    await ctx.send('Voice active: {}'.format(ctx.channel.guild.voice_client.is_playing()))

                else:

                    await ctx.send('Voice active: False')

            except:

                pass



            try:

                await ctx.send('Voice active in servers: {}'.format(len(self.bot.voice_clients)))

            except:

                pass



    @commands.command(aliases=['playlistadd', 'listadd'])
    async def _playlistAdd(self, ctx):



        message = ctx.message.content[ctx.message.content.index(' ') + 1:]



        playlist = message[:message.index(' ')]



        message = message[message.index(' ') + 1:]



        file = open('{}/{}'.format(ctx.channel.guild.id, playlist), "a")



        file.write('{}\n'.format(message))

        file.close()



        await ctx.send('Song added to server playlist')





    @commands.command(aliases=['playlistremove', 'listremove'])
    async def _playlistRemove(self, ctx):



        message = ctx.message.content[ctx.message.content.index(' ') + 1:]



        playlist = message[:message.index(' ')]



        message = message[message.index(' ') + 1:]



        fileR = open('{}/{}'.format(ctx.channel.guild.id, playlist), "r")



        lines = fileR.readlines()

        fileR.close()

        file = open('{}/{}'.format(ctx.channel.guild.id, playlist))

        for line in lines:

            if line.strip("\n") != message:



                file.write(line)



            else:

                await ctx.send('Removed one instance of the song')



                message = None    



        file.close()



        if os.stat('{}/{}'.format(ctx.channel.guild.id, playlist)).st_size == 0:

            os.remove('{}/{}'.format(ctx.channel.guild.id, playlist))





    @commands.command(aliases=['l', 'loop'])
    async def _loop(self, ctx):



        if not ctx.author.bot:



            server = ctx.message.guild

            voice_channel = server.voice_client

            channel = ctx.author.voice.channel



            if ctx.author.voice == None:

                await ctx.send('You are not in a voice channel')

                return



            if server.voice_client.channel != ctx.author.voice.channel:



                if len(server.voice_client.channel.members) > 1:

                    await ctx.send('You have to be in the same voice channel')

                    return



        try:

            self.looping[ctx.channel.guild.id] = not self.looping[ctx.channel.guild.id]

        except:

            self.looping[ctx.channel.guild.id] = True



        if self.looping[ctx.channel.guild.id] is True:

            await ctx.send('Looping')

        else:

            await ctx.send('No longer self.looping')



    @commands.command()
    async def pause(self, ctx):

        if not ctx.author.bot:



            server = ctx.message.guild



            if server.voice_client.channel != ctx.author.voice.channel:

                return



            server.voice_client.pause()



    @commands.command(aliases=['continue', 'resume'])
    async def _resume(self, ctx):

        if not ctx.author.bot:



            server = ctx.message.guild



            if server.voice_client.channel != ctx.author.voice.channel:

                return



            server.voice_client.resume()



    @commands.command(aliases=['q', 'queue'])
    async def _queue(self, ctx):

        if self.queue.get(ctx.channel.guild.id):



            embedVar = discord.Embed(title="Queue", color=0x0e41b5)

            embedVar.description = ''

            for video in self.queue.get(ctx.channel.guild.id):

                embedVar.description += video.replace('+', ' ') + '\n'

            await ctx.send(embed=embedVar)



    @commands.command(aliases=['s', 'skip'])
    async def _skip(self, ctx):

        if not ctx.author.bot:



            server = ctx.message.guild



            if server.voice_client.channel != ctx.author.voice.channel:

                return



            try:

                self.skips[server.id] += 1

            except:

                self.skips[server.id] = 1



            if self.skips[server.id] >= (len(server.voice_client.channel.members)) - 1 / 2:

                server.voice_client.stop()

                await ctx.send('Skipping')

                del(self.skips[server.id])



                del(self.video_ids[ctx.channel.guild.id][0])



                if len(self.video_ids[ctx.channel.guild.id]) == 0:

                    del(self.video_ids[ctx.channel.guild.id])



                    return



            elif len(server.voice_client.channel.members) - 1 <= 2:

                server.voice_client.stop()

                await ctx.send('Skipping')

                del(self.skips[server.id])



                del(self.video_ids[ctx.channel.guild.id][0])



                if len(self.video_ids[ctx.channel.guild.id]) == 0:

                    del(self.video_ids[ctx.channel.guild.id])



                    return



            else:

                await ctx.send('{}/{}'.format(self.skips[server.id], round((len(server.voice_client.channel.members)) - 1 / 2)))



    @commands.command(aliases=['fs', 'fskip', 'fastskip', 'forceskip'])
    async def _fskip(self, ctx):

        if not ctx.author.bot:



            for i in ctx.author.roles:

                    if i.name.lower() == 'dj':

                        if not ctx.author.guild_permissions.administrator:

                            return



            server = ctx.message.guild



            if server.voice_client.channel != ctx.author.voice.channel:

                return



            server.voice_client.stop()

            await ctx.send('Skipping')



            if len(self.video_ids[i.guild.id]) <= 1:

                del(self.video_ids[i.guild.id])

                del(self.queue[i.guild.id])



                return



    @commands.command(aliases=['r', 'remove'])
    async def _remove(self, ctx):

        if not ctx.author.bot:



            for i in ctx.author.roles:

                    if i.name.lower() == 'dj':

                        if not ctx.author.guild_permissions.administrator:

                            return



            index = int(ctx.message.content[ctx.message.content.index(' ') + 1:])



            server = ctx.message.guild



            if self.queue.get(server.id):

                del(self.queue[server.id][index - 1])

            if self.video_ids.get(server.id):

                del(self.video_ids[server.id][index - 1])





            if server.voice_client.channel != ctx.author.voice.channel:

                return



            await ctx.send('Removed at {}'.format(index))



    @commands.command(aliases=['p', 'play'])
    async def _play(self, ctx):



        if not ctx.author.bot:



            if ctx.author.voice == None:

                await ctx.send('You are not in a voice channel')

                return



            server = ctx.message.guild

            voice_channel = server.voice_client

            channel = ctx.author.voice.channel



            name = urllib.parse.quote_plus(ctx.message.content[ctx.message.content.index(' ') + 1:])



            if name == '':

                await ctx.send('You must specify the name of the video')

                return



            if server.voice_client == None:

                await channel.connect()

                voice_channel = server.voice_client



            elif not server.voice_client.is_connected():

                await channel.connect()

                voice_channel = server.voice_client



            if server.voice_client.channel != ctx.author.voice.channel:



                if len(server.voice_client.channel.members) > 1:

                    await ctx.send('You have to be in the same voice channel')

                    return

                else:

                    server.voice_client.disconnect()

                    await channel.connect()

            if re.match(r"https://open.spotify.com/playlist/(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):

                try:

                    searchterms = self.spotify_to_youtube(ctx.message.content[ctx.message.content.index(' ') + 1:])

                except:

                    await ctx.send('Invalid link')



                if ctx.author.voice == None:

                    await ctx.send('You are not in a voice channel')

                    return



                server = ctx.message.guild

                voice_channel = server.voice_client

                channel = ctx.author.voice.channel



                name = urllib.parse.quote_plus(ctx.message.content[ctx.message.content.index(' ') + 1:])



                if server.voice_client == None:

                    await channel.connect()

                    voice_channel = server.voice_client



                elif not server.voice_client.is_connected():

                    await channel.connect()

                    voice_channel = server.voice_client



                if server.voice_client.channel != ctx.author.voice.channel:



                    if len(server.voice_client.channel.members) > 1:

                        await ctx.send('You have to be in the same voice channel')

                        return

                    else:

                        server.voice_client.disconnect()

                        await channel.connect()



                for i in searchterms:

                    i = urllib.parse.quote_plus(i)

                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)



                    try:

                        self.queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0])

                    except:

                        self.queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0]]



                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)



                    try:

                        self.video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                    except:

                        self.video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]



            #///////////////////////////Playlists below



            elif re.match(r"https://www.youtube.com/playlist\?list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):



                html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])



                playList = re.findall(r'"title":"([^"]+)', html.read().decode())[0]



                html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])            



                try:

                    self.queue[server.id].extend(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode()))

                except:

                    self.queue[server.id] = ['a']

                    self.queue[server.id].extend(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode()))

                    del(self.queue[server.id][0])



                html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])



                try:

                    self.video_ids[server.id].extend(re.findall(r"watch\?v=(\S{11})", html.read().decode()))

                except:

                    self.video_ids[server.id] = ['a']

                    self.video_ids[server.id].extend(re.findall(r"watch\?v=(\S{11})", html.read().decode()))

                    del(self.video_ids[server.id][0])



                song = pafy.new(self.video_ids[server.id][0])



                audio = song.getbestaudio()



                if not voice_channel.is_playing():



                    voice_channel.play(discord.FFmpegPCMAudio(audio.url, **self.ffmpegPCM_options), after=lambda e: self.stop_playing(server))

                    await ctx.send('Now playing from playlist: {}'.format(playList))



                    del(self.queue[server.id][0])



                    if len(self.queue[server.id]) == 0:

                        del(self.queue[server.id])



            #/////////////////////Playlists ^



            else:

                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)



                try:

                    self.queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0])

                except:

                    self.queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0]]



                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)



                try:

                    self.video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                except:

                    self.video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]





            song = pafy.new(self.video_ids[server.id][0])



            #song.duration is an existing attribute



            audio = song.getbestaudio()



            if not voice_channel.is_playing():



                voice_channel.play(discord.FFmpegPCMAudio(audio.url, **self.ffmpegPCM_options), after=lambda e: self.stop_playing(server))

                await ctx.send('Now playing: {}'.format(urllib.parse.unquote(self.queue[server.id][0])))



                del(self.queue[server.id][0])



                if len(self.queue[server.id]) == 0:

                    del(self.queue[server.id])

    

def setup(bot):
    bot.add_cog(MainCog(bot))

