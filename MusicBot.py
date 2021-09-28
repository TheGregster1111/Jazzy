import sys

import discord

import discord.member

import discord.channel

import discord.message

import discord.voice_client

from discord.ext import commands, tasks

import os

import MusicBotConfig

import urllib.request

from urllib.parse import urlencode, urlparse, urlunparse

import urllib3

import re

import pafy

import datetime

import spotipy

from spotipy import SpotifyClientCredentials

print('Test file successfully run')

while True:
    try:

        discordIntents = discord.Intents.all()



        bot = commands.Bot(command_prefix=MusicBotConfig.prefix, intents=discordIntents)



        bot.remove_command('help')



        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(MusicBotConfig.client_id, MusicBotConfig.client_secret))



        video_ids = {}

        skips = {}

        queue = {}

        looping = {}

        autoDisconnect = []



        ffmpegPCM_options = {

            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 1000",

            'options': '-vn'

        }



        def spotify_to_youtube(playlistURL):



            results = spotify.playlist(playlist_id=playlistURL)



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



        def stop_playing(server):

            if looping.get(server.id):

                if looping[server.id] is False:

                    del(video_ids[server.id][0])



                    if len(video_ids[server.id]) == 0:

                        del(video_ids[server.id])

            else:

                del(video_ids[server.id][0])



                if len(video_ids[server.id]) == 0:

                    del(video_ids[server.id])



            try:

                server.voice_client.stop()

            except:

                if server.voice_client:

                    print('Something went wrong after the song stopped playing at {}'.format(datetime.datetime.now()))



            



























        @bot.event

        async def on_ready():

            playFromList.start()



            for filename in os.listdir(os.path.dirname(__file__) + '\\Music_Cogs'):
            
                if filename.endswith('.py'):
            
                    bot.load_extension(f'Music_Cogs.{filename[:-3]}')
                    
                    
            os.chdir('Playlists')



        @bot.event

        async def on_voice_state_update(member, before, after):

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

                if bot.get_channel(before.channel.id).members == [] and before.channel.name == "Temp VC":

                    await before.channel.delete()



            if before.channel and not member.id is bot.user.id and before.channel.guild.voice_client:

                if before.channel == before.channel.guild.voice_client.channel:

                    if len(before.channel.members) == 1:

                        await before.channel.guild.voice_client.disconnect()



                        if queue.get(before.channel.guild.id):

                            del(queue[before.channel.guild.id])

                        if video_ids.get(before.channel.guild.id):

                            del(video_ids[before.channel.guild.id])

                        if looping.get(before.channel.guild.id):

                            del(looping[before.channel.guild.id])



        @bot.event

        async def on_guild_join(guild):

            os.mkdir(str(guild.id), 'w')



        @bot.event

        async def on_guild_remove(guild):

            os.mkdir(str(guild.id), 'w')



        @tasks.loop(seconds=0.1)

        async def shutDown():

            if MusicBotConfig.shutdown is True:

                sys.exit()



        @tasks.loop(seconds=5)

        async def playFromList():

            for i in bot.voice_clients:

                if not i.is_playing() and video_ids.get(i.guild.id):



                    song = pafy.new(video_ids[i.guild.id][0])



                    try:

                        del(queue[i.guild.id][0])



                        if len(queue[i.guild.id]) == 0:

                            del(queue[i.guild.id])

                    except:

                        pass



                    audio = song.getbestaudio()

                    i.guild.voice_client.play(discord.FFmpegPCMAudio(audio.url, **ffmpegPCM_options), after=lambda e: stop_playing(i.guild))



        @bot.command()

        async def help(ctx):

            embedVar = discord.Embed(title="Commands", color=0x0e41b5)

            embedVar.add_field(name='!play !p', value='Play the audio of a youtube song, playlist, or spotify playlist', inline=False)

            embedVar.add_field(name='!skip !s', value='Skip current song', inline=False)

            embedVar.add_field(name='!fs !fskip !fastskip !forceskip', value='Instantly skip current song, only useable by someone with a role named DJ or an admin', inline=False)

            embedVar.add_field(name='!queue !q', value='View the current queue', inline=False)

            embedVar.add_field(name='!remove !r', value='Remove the specified song from the queue, example: !remove 2', inline=False)

            embedVar.add_field(name='!reset', value='Reset the bot if it is malfunctioning', inline=False)

            embedVar.add_field(name='!pause', value='Pause the song', inline=False)

            embedVar.add_field(name='!continue !resume', value='Resume the song', inline=False)

            embedVar.add_field(name='!loop', value='Starts or stops looping the song', inline=False)

            embedVar.add_field(name='Extra stuff', value='Try making a new voice channel named "Create VC" and connecting to it', inline=False)

            await ctx.send(embed=embedVar)



        @bot.command()

        async def reset(ctx):



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

                del(queue[ctx.channel.guild.id])

            except:

                pass

            try:

                del(video_ids[ctx.channel.guild.id])

            except:

                pass



        @bot.command()

        async def debug(ctx):

            if ctx.author.id == 320837660900065291:



                try:

                    embedVar = discord.Embed(title="Visible queue", color=0x0e41b5)

                    embedVar.description = ''

                    for video in queue.get(ctx.channel.guild.id):

                        embedVar.description += video.replace('+', ' ') + '\n'

                    await ctx.send(embed=embedVar)

                except:

                    pass

                

                try:

                    embedVar = discord.Embed(title="Hidden queue", color=0x0e41b5)

                    embedVar.description = ''

                    for video in video_ids.get(ctx.channel.guild.id):

                        embedVar.description += video.replace('+', ' ') + '\n'

                    await ctx.send(embed=embedVar)

                except:

                    pass



                try:

                    if looping.get(ctx.channel.guild.id):

                        await ctx.send(looping[ctx.channel.guild.id])

                    else:

                        await ctx.send(False)

                except:

                    pass

                

                try:

                    if ctx.channel.guild.voice_client:

                        await ctx.send(ctx.channel.guild.voice_client.is_playing())

                    else:

                        await ctx.send(False)

                except:

                    pass

                    

        @bot.command(aliases=['playlistadd', 'listadd'])

        async def _playlistAdd(ctx):



            message = ctx.message.content[ctx.message.content.index(' ') + 1:]



            playlist = message[:message.index(' ')]



            message = message[message.index(' ') + 1:]



            file = open('{}\\{}'.format(ctx.channel.guild.id, playlist), "a")



            file.write('{}\n'.format(message))

            file.close()



            await ctx.send('Song added to server playlist')





        @bot.command(aliases=['playlistremove', 'listremove'])

        async def _playlistRemove(ctx):



            message = ctx.message.content[ctx.message.content.index(' ') + 1:]



            playlist = message[:message.index(' ')]



            message = message[message.index(' ') + 1:]



            fileR = open('{}\\{}'.format(ctx.channel.guild.id, playlist), "r")



            lines = fileR.readlines()

            fileR.close()

            file = open('{}\\{}'.format(ctx.channel.guild.id, playlist))

            for line in lines:

                if line.strip("\n") != message:



                    file.write(line)



                else:

                    await ctx.send('Removed one instance of the song')



                    message = None    



            file.close()



            if os.stat('{}\\{}'.format(ctx.channel.guild.id, playlist)).st_size == 0:

                os.remove('{}\\{}'.format(ctx.channel.guild.id, playlist))





        @bot.command(aliases=['l', 'loop'])

        async def _loop(ctx):



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

                looping[ctx.channel.guild.id] = not looping[ctx.channel.guild.id]

            except:

                looping[ctx.channel.guild.id] = True



            if looping[ctx.channel.guild.id] is True:

                await ctx.send('Looping')

            else:

                await ctx.send('No longer looping')



        @bot.command()

        async def pause(ctx):

            if not ctx.author.bot:



                server = ctx.message.guild



                if server.voice_client.channel != ctx.author.voice.channel:

                    return

                

                server.voice_client.pause()



        @bot.command(aliases=['continue', 'resume'])

        async def _resume(ctx):

            if not ctx.author.bot:



                server = ctx.message.guild



                if server.voice_client.channel != ctx.author.voice.channel:

                    return

                

                server.voice_client.resume()



        @bot.command(aliases=['q', 'queue'])

        async def _queue(ctx):

            if queue.get(ctx.channel.guild.id):



                embedVar = discord.Embed(title="Queue", color=0x0e41b5)

                embedVar.description = ''

                for video in queue.get(ctx.channel.guild.id):

                    embedVar.description += video.replace('+', ' ') + '\n'

                await ctx.send(embed=embedVar)



        @bot.command(aliases=['s', 'skip'])

        async def _skip(ctx):

            if not ctx.author.bot:



                server = ctx.message.guild



                if server.voice_client.channel != ctx.author.voice.channel:

                    return

                

                try:

                    skips[server.id] += 1

                except:

                    skips[server.id] = 1



                if skips[server.id] >= (len(server.voice_client.channel.members)) - 1 / 2:

                    server.voice_client.stop()

                    await ctx.send('Skipping')

                    del(skips[server.id])



                    del(video_ids[ctx.channel.guild.id][0])



                    if len(video_ids[ctx.channel.guild.id]) == 0:

                        del(video_ids[ctx.channel.guild.id])



                        return

                    

                elif len(server.voice_client.channel.members) - 1 <= 2:

                    server.voice_client.stop()

                    await ctx.send('Skipping')

                    del(skips[server.id])

                    

                    del(video_ids[ctx.channel.guild.id][0])



                    if len(video_ids[ctx.channel.guild.id]) == 0:

                        del(video_ids[ctx.channel.guild.id])



                        return



                else:

                    await ctx.send('{}/{}'.format(skips[server.id], round((len(server.voice_client.channel.members)) - 1 / 2)))



        @bot.command(aliases=['fs', 'fskip', 'fastskip', 'forceskip'])

        async def _fskip(ctx):

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



                if len(video_ids[i.guild.id]) <= 1:

                    del(video_ids[i.guild.id])

                    del(queue[i.guild.id])



                    return



        @bot.command(aliases=['r', 'remove'])

        async def _remove(ctx):

            if not ctx.author.bot:



                for i in ctx.author.roles:

                        if i.name.lower() == 'dj':

                            if not ctx.author.guild_permissions.administrator:

                                return



                index = int(ctx.message.content[ctx.message.content.index(' ') + 1:])



                server = ctx.message.guild



                if queue.get(server.id):

                    del(queue[server.id][index - 1])

                if video_ids.get(server.id):

                    del(video_ids[server.id][index - 1])

                



                if server.voice_client.channel != ctx.author.voice.channel:

                    return



                await ctx.send('Removed at {}'.format(index))



        @bot.command(aliases=['p', 'play'])

        async def _play(ctx):



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

                await ctx.send(ctx.message.content[ctx.message.content.index(' ') + 1:])

                if re.match(r"https://open.spotify.com/playlist/(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):

                    await ctx.send('True')

                    try:

                        searchterms = spotify_to_youtube(ctx.message.content[ctx.message.content.index(' ') + 1:])

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

                            queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0])

                        except:

                            queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0]]



                        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)



                        try:

                            video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                        except:

                            video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]



                #///////////////////////////Playlists below



                elif re.match(r"https://www.youtube.com/playlist\?list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):

                    

                    html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])



                    playList = re.findall(r'"title":"([^"]+)', html.read().decode())[0]

                    

                    html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])            



                    try:

                        queue[server.id].extend(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode()))

                    except:

                        queue[server.id] = ['a']

                        queue[server.id].extend(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode()))

                        del(queue[server.id][0])



                    html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])



                    try:

                        video_ids[server.id].extend(re.findall(r"watch\?v=(\S{11})", html.read().decode()))

                    except:

                        video_ids[server.id] = ['a']

                        video_ids[server.id].extend(re.findall(r"watch\?v=(\S{11})", html.read().decode()))

                        del(video_ids[server.id][0])



                    song = pafy.new(video_ids[server.id][0])



                    audio = song.getbestaudio()

                

                    if not voice_channel.is_playing():



                        voice_channel.play(discord.FFmpegPCMAudio(audio.url, **ffmpegPCM_options), after=lambda e: stop_playing(server))

                        await ctx.send('Now playing from playlist: {}'.format(playList))



                        del(queue[server.id][0])



                        if len(queue[server.id]) == 0:

                            del(queue[server.id])



                #/////////////////////Playlists ^

                

                else:

                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)



                    try:

                        queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0])

                    except:

                        queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"([^"]+)', html.read().decode())[0]]



                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)



                    try:

                        video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                    except:

                        video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]

                    



                song = pafy.new(video_ids[server.id][0])



                #song.duration is an existing attribute



                audio = song.getbestaudio()

                

                if not voice_channel.is_playing():



                    voice_channel.play(discord.FFmpegPCMAudio(audio.url, **ffmpegPCM_options), after=lambda e: stop_playing(server))

                    print(queue[server.id][0])

                    await ctx.send('Now playing: {}'.format(urllib.parse.unquote(queue[server.id][0])))



                    del(queue[server.id][0])



                    if len(queue[server.id]) == 0:

                        del(queue[server.id])

                        

        bot.run(MusicBotConfig.token)



    except Exception:

        pass

