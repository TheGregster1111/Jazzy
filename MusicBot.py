import discord
import discord.member
import discord.channel
import discord.message
import discord.voice_client
from discord.ext import commands, tasks
from discord_components import Button, ButtonStyle
import os
import MusicBotConfig
import urllib.request
import re
import pafy
import datetime
import spotipy
from spotipy import SpotifyClientCredentials
from threading import Thread

print('Test file successfully run')

class MainCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.playFromList.start()

        for filename in os.listdir(os.path.dirname(__file__) + '/Music_Cogs'):

            if filename.endswith('.py'):

                self.bot.load_extension(f'Music_Cogs.{filename[:-3]}')

        try:
            os.chdir('source/repos/MusicBot')
        except:
            pass

        os.chdir('Playlists')

    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(MusicBotConfig.client_id, MusicBotConfig.client_secret))

    global video_ids

    video_ids = {}
    
    skips = {}

    global queue

    queue = {}

    looping = {}

    global serverplaylist

    serverplaylist = None

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

    

    def add_to_queue(self, searchterms, server):

        global video_ids
        global queue

        counter = 0

        for i in searchterms:

            counter += 1

            i = urllib.parse.quote_plus(i)

            html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)

            try:

                queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_'))

            except:
                
                if counter >= 2:
                    return

                queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_')]



            html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)

            

            try:

                video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

            except:

                if counter >= 2:
                    return

                video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]



    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        global queue
        global video_ids

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



                    if queue.get(before.channel.guild.id):

                        del(queue[before.channel.guild.id])

                    if video_ids.get(before.channel.guild.id):

                        del(video_ids[before.channel.guild.id])

                    if self.looping.get(before.channel.guild.id):

                        del(self.looping[before.channel.guild.id])



    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        try:
            os.chdir('/home/pi/MusciBot/Playlists')
        except:
            pass

        os.mkdir(str(guild.id), 'w')

        os.chdir('..')



    @commands.Cog.listener()
    async def on_guild_remove(self, guild):

        try:
            os.chdir('/home/pi/MusciBot/Playlists')
        except:
            pass

        os.mkdir(str(guild.id), 'w')

        os.chdir('..')



    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(error)



    @tasks.loop(seconds=5)
    async def playFromList(self):

        global queue
        global video_ids

        for i in self.bot.voice_clients:

            if not i.is_playing() and video_ids.get(i.guild.id):



                song = pafy.new(video_ids[i.guild.id][0])



                try:

                    del(queue[i.guild.id][0])



                    if len(queue[i.guild.id]) == 0:

                        del(queue[i.guild.id])

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

        embedVar.add_field(name='!queue !q', value='View the current queue', inline=False)

        embedVar.add_field(name='!remove !r', value='Remove the specified song from the queue, example: !remove 2', inline=False)

        embedVar.add_field(name='!reset', value='Reset the bot if it is malfunctioning', inline=False)

        embedVar.add_field(name='!pause', value='Pause the song', inline=False)

        embedVar.add_field(name='!continue !resume', value='Resume the song', inline=False)

        embedVar.add_field(name='!loop', value='Starts or stops self.looping the song', inline=False)
        
        embedVar.add_field(name='!playlistplay !listplay', value='Use "!listplay `Playlist name`" to play songs from a server playlist', inline=False)

        embedVar.add_field(name='!playlistadd !listadd', value='Use "!listadd `Playlist name` `Song name`" to add a song to a server playlist', inline=False)

        embedVar.add_field(name='!playlistremove !listremove', value='Use "!listremove `Playlist name` `Song name`" to remove a song from a server playlist', inline=False)

        embedVar.add_field(name='!removeplaylist !removelist', value='Use "!removelist `Playlist name`" to remove a server playlist', inline=False)

        embedVar.add_field(name='!playlists !lists', value='View all server playlists', inline=False)

        embedVar.add_field(name='!playlist !list', value='Use "!list `Playlist name`" to view all songs in specified playlist', inline=False)

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
                style = ButtonStyle.URL,
                url = 'https://discord.gg/qpP4CZABJx'
            ),
            Button(
                label = "Invite",
                style = ButtonStyle.URL,
                url = 'https://discord.com/api/oauth2/authorize?client_id=887684182975840296&permissions=0&scope=bot'
            )
            ]
            ]
        )


    @commands.command()
    async def reset(self, ctx):

        global queue
        global video_ids

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

            global queue
            global video_ids

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



    @commands.command(aliases=['playlistplay', 'listplay'])
    async def _playlistplay(self, ctx):
        global serverplaylist

        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        file = open('{}/{}'.format(str(ctx.channel.guild.id), playlist), 'r')
        serverplaylist = []
        for line in file.readlines():
            serverplaylist.append(re.findall(r'"id":"{\[(.*?)\]}"', line)[0])

        print(serverplaylist)

        await self._play(ctx)

    @commands.command(aliases=['playlist', 'list'])
    async def _playlist(self, ctx):
        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        file = open('{}/{}'.format(str(ctx.channel.guild.id), playlist), 'r')

        lines = file.readlines()

        file.close()

        embedVar = discord.Embed(title="Server playlists", color=0x0e41b5)

        embedVar.description = ''

        for line in lines:

            embedVar.description += re.findall(r'"title":"{\[(.*?)\]}"', line)[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_') + '\n\n'


        await ctx.send(embed=embedVar)

    @commands.command(aliases=['playlists', 'lists'])
    async def _playlists(self, ctx):
        
        embedVar = discord.Embed(title="Server playlists", color=0x0e41b5)

        embedVar.description = ''

        for file in os.listdir(str(ctx.channel.guild.id)):

            os.chdir(str(ctx.channel.guild.id))

            embedVar.description += file + ', {} songs'.format(len(open(file, 'r').readlines()))

            os.chdir('..')

        await ctx.send(embed=embedVar)

    @commands.command(aliases=['playlistadd', 'listadd'])
    async def _playlistAdd(self, ctx):

        for i in ctx.author.roles:

            if i.name.lower() == 'dj':

                if not ctx.author.guild_permissions.administrator:

                    return

        if len(os.listdir(ctx.channel.guild.id)) >= 20:
            await ctx.send('Maximum number of 20 playlists already reached')

        message = ctx.message.content[ctx.message.content.index(' ') + 1:]

        playlist = message[:message.index(' ')]

        message = urllib.parse.quote_plus(message[message.index(' ') + 1:])

        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + message)
        
        video_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]

        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + message)

        video_name = urllib.parse.unquote(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0])

        file = open('{}/{}'.format(ctx.channel.guild.id, playlist), "a")

        file.write('"title":"{{[{}]}}", "id":"{{[{}]}}"\n'.format(video_name, video_id))

        file.close()

        await ctx.send('`{}` added to server playlist `{}`'.format(video_name, playlist))



    @commands.command(aliases=['removeplaylist', 'removelist'])
    async def _RemovePlaylist(self, ctx):
        for i in ctx.author.roles:

            if i.name.lower() == 'dj':

                if not ctx.author.guild_permissions.administrator:

                    return

        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        try:        
            os.remove('{}/{}'.format(ctx.channel.guild.id, playlist))
        
        except:
            await ctx.send('Playlist {} could not be successfully deleted'.format(playlist))
            return

        await ctx.send('Playlist {} was successfully deleted'.format(playlist))

    @commands.command(aliases=['playlistremove', 'listremove'])
    async def _playlistRemove(self, ctx):

        for i in ctx.author.roles:

            if i.name.lower() == 'dj':

                if not ctx.author.guild_permissions.administrator:

                    return

        message = ctx.message.content[ctx.message.content.index(' ') + 1:]

        playlist = message[:message.index(' ')]

        message = urllib.parse.quote_plus(message[message.index(' ') + 1:])

        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + message)
        
        video_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]

        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + message)

        video_name = urllib.parse.unquote(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0])

        fileR = open('{}/{}'.format(ctx.channel.guild.id, playlist), "r")

        lines = fileR.readlines()

        fileR.close()

        file = open('{}/{}'.format(ctx.channel.guild.id, playlist), 'w')

        for line in lines:

            print(line + ' ////////// ' + '"title":"{{[{}]}}", "id":"{{[{}]}}"\n'.format(video_name, video_id))

            if '"title":"{{[{}]}}", "id":"{{[{}]}}"\n'.format(video_name, video_id) != line:

                file.write(line)



            else:

                await ctx.send('Removed one instance of the song')



                video_name = None
                video_id = None



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

        if queue.get(ctx.channel.guild.id):



            embedVar = discord.Embed(title="Queue", color=0x0e41b5)

            embedVar.description = ''

            for video in queue.get(ctx.channel.guild.id):

                embedVar.description += video.replace('+', ' ') + '\n'

            await ctx.send(embed=embedVar)



    @commands.command(aliases=['s', 'skip'])
    async def _skip(self, ctx):

        if not ctx.author.bot:

            global queue
            global video_ids

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



                del(video_ids[ctx.channel.guild.id][0])



                if len(video_ids[ctx.channel.guild.id]) == 0:

                    del(video_ids[ctx.channel.guild.id])



                    return



            elif len(server.voice_client.channel.members) - 1 <= 2:

                server.voice_client.stop()

                await ctx.send('Skipping')

                del(self.skips[server.id])



                del(video_ids[ctx.channel.guild.id][0])



                if len(video_ids[ctx.channel.guild.id]) == 0:

                    del(video_ids[ctx.channel.guild.id])



                    return



            else:

                await ctx.send('{}/{}'.format(self.skips[server.id], round((len(server.voice_client.channel.members)) - 1 / 2)))



    @commands.command(aliases=['fs', 'fskip', 'fastskip', 'forceskip'])
    async def _fskip(self, ctx):

        if not ctx.author.bot:

            global queue
            global video_ids

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



    @commands.command(aliases=['r', 'remove'])
    async def _remove(self, ctx):

        if not ctx.author.bot:

            global queue
            global video_ids

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



    @commands.command(aliases=['p', 'play'])
    @commands.cooldown(1.0, 10.0, commands.BucketType.guild)
    async def _play(self, ctx):

        global serverplaylist
        global queue
        global video_ids

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

                    if queue.get(ctx.guild.id):
                        if len(queue[ctx.guild.id]) + len(searchterms) >= 30:
                            await ctx.send('Maximum queue size reached')

                            searchterms = searchterms[:30 - len(queue[ctx.guild.id])]

                    else:
                        if len(searchterms) >= 30:
                            await ctx.send('Maximum queue size reached')

                            searchterms = searchterms[:30]
                except:

                    await ctx.send('Invalid link')

                if ctx.author.voice == None:

                    await ctx.send('You are not in a voice channel')

                    return



                server = ctx.message.guild

                voice_channel = server.voice_client

                channel = ctx.author.voice.channel



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



                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(searchterms[0]))

                try:

                    queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_'))

                except:

                    queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_')]



                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(searchterms[0]))



                try:

                    video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                except:

                    video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]

                searchterms = searchterms[1:]

                thread = Thread(target = self.add_to_queue, args = (searchterms, server))
                thread.start()


            #///////////////////////////Playlists below



            elif re.match(r"https://www.youtube.com/playlist\?list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):

                html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])



                playList = re.findall(r'"title":"(.*?)"}\]', html.read().decode())[0]



                html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])



                try:

                    queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_'))

                except:

                    queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_')]

                    del(queue[server.id][0])



                html = urllib.request.urlopen(ctx.message.content[ctx.message.content.index(' ') + 1:])



                try:

                    video_ids[server.id].extend(re.findall(r"watch\?v=(\S{11})", html.read().decode()))

                except:

                    video_ids[server.id].extend(re.findall(r"watch\?v=(\S{11})", html.read().decode()))

                    del(video_ids[server.id][0])



                song = pafy.new(video_ids[server.id][0])



                audio = song.getbestaudio()



                if not voice_channel.is_playing():



                    voice_channel.play(discord.FFmpegPCMAudio(audio.url, **self.ffmpegPCM_options), after=lambda e: self.stop_playing(server))

                    await ctx.send('Now playing from playlist: {}'.format(playList))



                    del(queue[server.id][0])



                    if len(queue[server.id]) == 0:

                        del(queue[server.id])



            #/////////////////////Playlists ^



            elif serverplaylist is not None:
                
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



                for i in serverplaylist:

                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)

                    try:

                        queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_'))

                    except:

                        queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_')]



                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)



                    try:

                        video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                    except:

                        video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]

                serverplaylist = None
                    

            else:

                if queue.get(ctx.guild.id): #//START

                    if len(queue[ctx.guild.id]) >= 30:
                        await ctx.send('Maximum queue size reached')

                    if len(queue[ctx.guild.id]) + len(serverplaylist) >= 30:
                        await ctx.send('Maximum queue size reached')

                        serverplaylist = serverplaylist[:len(queue[ctx.guild.id]) - len(serverplaylist)] #//////FOR LATER
                
                    elif len(serverplaylist) >= 30:
                        await ctx.send('Maximum queue size reached')

                        serverplaylist = serverplaylist[:30] #//END
                        

                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)

                try:

                    queue[server.id].append(urllib.parse.unquote(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_')))

                except:

                    queue[server.id] = [urllib.parse.unquote(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_'))]



                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)



                try:

                    video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                except:

                    video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]


            song = pafy.new(video_ids[server.id][0])



            #song.duration is an existing attribute



            audio = song.getbestaudio()



            if not voice_channel.is_playing():



                voice_channel.play(discord.FFmpegPCMAudio(audio.url, **self.ffmpegPCM_options), after=lambda e: self.stop_playing(server))

                await ctx.send('Now playing: {}'.format(urllib.parse.unquote(queue[server.id][0])))



                del(queue[server.id][0])



                if len(queue[server.id]) == 0:

                    del(queue[server.id])

                if len(queue[ctx.guild.id]) >= 30:
                    await ctx.send('Maximum queue size reached')

                    queue = queue[:30]

    @_play.error
    async def _play_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('!play is on cooldown to avoid slowing down bot')


    

def setup(bot):
    bot.add_cog(MainCog(bot))

