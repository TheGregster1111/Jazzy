import discord
from discord.enums import MessageType
from discord.ext import commands, tasks
from discord.ui.button import Button
import os
import random
import MusicBotConfig
import urllib.request
import re
import pafy
import datetime
import spotipy
from spotipy import SpotifyClientCredentials
from threading import Thread
import yt_dlp

#regex dictionary
#(.*?)    match unspecified length of characters
#(?:.*?)    ignore unspecified length of characters
#() Will add the contents to the list and is not necessary for .*? to work

class MainCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.playFromList.start()
        #self.clear.start()

        os.chdir(os.path.dirname(__file__))

        try:
            os.chdir('../Playlists')
        except:
            os.mkdir('../Playlists')
            os.chdir('../laylists')

    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(MusicBotConfig.client_id, MusicBotConfig.client_secret))
    pafy.set_api_key(MusicBotConfig.ytKey)

    global video_ids
    video_ids = {}
    
    skips = {}

    skipers = {}

    global queue
    queue = {}

    looping = {}

    global serverplaylist
    serverplaylist = None

    global locked
    locked = {}

    global maxSize

    global searchterms
    searchterms = {}

    global errorLog
    errorLog = {}
    
    maxSize = 61

    ffmpegPCM_options = {

        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2000",

        'options': '-vn'

    }



    def spotify_to_youtube(self, URL, type):

        trackList = []

        if type == 1:

            results = self.spotify.playlist(playlist_id=URL)

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

        elif type == 2:

            print('URL: ' + URL)

            results = self.spotify.track(track_id=URL)

            trackList = [results["name"] + " - " + results["artists"][0]["name"]]

        return trackList



    def stop_playing(self, server):
        global errorLog

        errorLog[server.id][0] += '\n\n[{}]   Stopped playing song. Queue count: `{}` ID count: `{}`'.format(datetime.datetime.now().time().strftime('%H:%M:%S'), len(queue[server.id]), len(video_ids[server.id]))

        if self.looping.get(server.id):

            if self.looping[server.id] is False:

                try:

                    del(queue[server.id][0])



                    if len(queue[server.id]) == 0:

                        del(queue[server.id])

                except:

                    pass

                try:

                    del(video_ids[server.id][0])



                    if len(video_ids[server.id]) == 0:

                        del(video_ids[server.id])

                except:

                    pass

        else:

            try:

                del(queue[server.id][0])



                if len(queue[server.id]) == 0:

                    del(queue[server.id])

            except:

                pass

            try:

                del(video_ids[server.id][0])



                if len(video_ids[server.id]) == 0:

                    del(video_ids[server.id])

            except:

                pass



        try:

            server.voice_client.stop()

        except:

            if server.voice_client:

                print('Something went wrong after the song stopped playing at {}'.format(datetime.datetime.now()))

        

        self.playFromList()
    

    def add_to_queue(self, searchterms, server, ctx:commands.context):

        global video_ids
        global queue

        counter = 0

        for i in searchterms[server.id]:

            counter += 1

            i = urllib.parse.quote_plus(i)

            html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)

            try:

                queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&') + datetime.datetime.now().time().strftime('%H:%M:%S'))

            except:
                
                if counter >= 2:
                    del(locked[server.id])
                    #await ctx.send("Playlist added to queue")
                    return

                queue[server.id] = [re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&')]



            html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)

            

            try:

                video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

            except:

                if counter >= 2:
                    del(locked[server.id])
                    #await ctx.send("Playlist added to queue")
                    return

                video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]
        
        del(locked[server.id])
        #await ctx.send("Playlist added to queue")



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

            if (await self.bot.fetch_channel(before.channel.id)).members == [] and before.channel.name == "Temp VC":

                await before.channel.delete()



        if before.channel and not member.id is self.bot.user.id and before.channel.guild.voice_client:

            if before.channel == before.channel.guild.voice_client.channel:

                membercount = 0

                for i in before.channel.members:
                    if not i.bot:
                        membercount += 1

                if membercount == 0:

                    await before.channel.guild.voice_client.disconnect()

                    if queue.get(before.channel.guild.id):

                        del(queue[before.channel.guild.id])

                    if video_ids.get(before.channel.guild.id):

                        del(video_ids[before.channel.guild.id])

                    if self.looping.get(before.channel.guild.id):

                        del(self.looping[before.channel.guild.id])



    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        os.chdir('/MusciBot/Playlists'.replace('/', os.path.sep))

        os.mkdir(str(guild.id), 'w')

        os.chdir('..')



    @commands.Cog.listener()
    async def on_guild_remove(self, guild):

        os.chdir('/MusciBot/Playlists'.replace('/', os.path.sep))

        os.rmdir(str(guild.id))

        os.chdir('..')



    @commands.Cog.listener()
    async def on_command_error(self, ctx:commands.context, error):
        print(error)

    @commands.Cog.listener()
    async def on_message(self, ctx:commands.context):
        if ctx.channel.id == MusicBotConfig.reportChannel and not ctx.author.bot:
            if ctx.type == MessageType.default and ctx.reference:
                if (ctx.content.lower().startswith('blacklist')):

                    ogMessage = await ctx.channel.fetch_message(ctx.reference.message_id)

                    #print(ogMessage.content)

                    if ctx.content[ctx.content.index(' ') + 1:].lower() == 'user':
                        userId = re.findall(r'\`(?:.*?)\` reported by \`(.*?)\` from server \`(?:.*?)\`', ogMessage.content)[0]
                        os.chdir("..")
                        file = open('blacklist_users.txt', 'a')
                        if not userId in open('blacklist_users.txt', 'r').read():
                            file.write(str(userId) + '\n')
                            await ctx.channel.send('User `{}` blacklisted'.format(await self.bot.fetch_user(userId)))
                        else:
                            await ctx.channel.send('User `{}` already blacklisted'.format(await self.bot.fetch_user(userId)))
                        file.close()
                        os.chdir("Playlists")
                    elif ctx.content[ctx.content.index(' ') + 1:].lower() == 'server':     
                        serverId = re.findall(r'\`(?:.*?)\` reported by \`(?:.*?)\` from server \`(.*?)\`', ogMessage.content)[0]
                        os.chdir("..")
                        file = open('blacklist_servers.txt', 'a')
                        if not serverId in open('blacklist_servers.txt', 'r').read():
                            file.write(str(serverId) + '\n')
                            await ctx.channel.send('Server `{}` blacklisted'.format(await self.bot.fetch_guild(serverId)))
                        else:
                            await ctx.channel.send('Server `{}` already blacklisted'.format(await self.bot.fetch_guild(serverId)))
                        file.close()
                        os.chdir("Playlists")

                elif (ctx.content.lower().startswith('unblacklist')):

                    ogMessage = await ctx.channel.fetch_message(ctx.reference.message_id)

                    #print(ogMessage.content)

                    if ctx.content[ctx.content.index(' ') + 1:].lower() == 'user':
                        userId = re.findall(r'\`(?:.*?)\` reported by \`(.*?)\` from server \`(?:.*?)\`', ogMessage.content)[0]
                        os.chdir("..")
                        file = open('blacklist_users.txt', 'a')
                        if not str(userId) in open('blacklist_users.txt', 'r').read():
                            await ctx.channel.send('User `{}` not blacklisted'.format(await self.bot.fetch_user(userId)))
                        else:
                            temp = open('blacklist_users.txt', 'r').readlines()
                            open('blacklist_users.txt', 'w').truncate()
                            for line in temp:
                                if line == '\n':
                                    pass
                                elif line.strip('\n') != str(userId):
                                    file.write(line)
                                else:
                                    await ctx.channel.send('User `{}` no longer blacklisted'.format(await self.bot.fetch_user(userId)))
                        file.write('\n')
                        file.close()
                        os.chdir("Playlists")
                    elif ctx.content[ctx.content.index(' ') + 1:].lower() == 'server':     
                        serverId = re.findall(r'\`(?:.*?)\` reported by \`(?:.*?)\` from server \`(.*?)\`', ogMessage.content)[0]
                        os.chdir("..")
                        file = open('blacklist_servers.txt', 'a')
                        if not str(serverId) in open('blacklist_servers.txt', 'r').read():
                            await ctx.channel.send('Server `{}` not blacklisted'.format(await self.bot.fetch_guild(serverId)))
                        else:
                            temp = open('blacklist_servers.txt', 'r').readlines()
                            open('blacklist_servers.txt', 'w').truncate()
                            for line in temp:
                                if line == '\n':
                                    pass
                                elif line.strip('\n') != str(serverId):
                                    file.write(line)
                                else:
                                    await ctx.channel.send('Server `{}` no longer blacklisted'.format(await self.bot.fetch_guild(serverId)))
                        file.write('\n')
                        file.close()
                        os.chdir("Playlists")



    @tasks.loop(minutes=5)
    async def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        #print('clear')


    @tasks.loop(seconds=5)
    async def playFromList(self):

        global queue
        global video_ids

        for i in self.bot.voice_clients:

            if not i.is_playing() and video_ids.get(i.guild.id):

                print('test')

                song = pafy.new(basic=False, gdata=False, url=video_ids[i.guild.id][0])

                audio = song.getbestaudio()

                i.guild.voice_client.play(discord.FFmpegPCMAudio(audio.url, **self.ffmpegPCM_options), after=lambda e: self.stop_playing(i.guild))



    


    @commands.command()
    async def reset(self, ctx:commands.context):

        global queue
        global video_ids
        global errorLog

        print('LogFile-{}.txt'.format(ctx.guild.name))

        try:
            reportChannel = await self.bot.fetch_channel(MusicBotConfig.reportChannel)

            os.chdir('..')

            log = open('LogFile-{}.txt'.format(ctx.guild.name), 'w')
            log.write(errorLog[ctx.guild.id][0])
            log.close()

            try:
                await reportChannel.send(file=discord.File('LogFile-{}.txt'.format(ctx.guild.name)))
            except:
                pass

            os.remove('LogFile-{}.txt'.format(ctx.guild.name))

            os.chdir('Playlists')

            await ctx.message.delete()
        except:
            pass

        if ctx.channel.guild.voice_client:

            if not len(ctx.channel.guild.voice_client.channel.members) - 1 <= 2:
                        
                if not ctx.author.guild_permissions.administrator:
                    
                    temp = False

                    for i in ctx.author.roles:

                        if i.name.lower() == 'dj':

                            temp = True

                    if not temp:
                        return

        await ctx.send('Resetting')
        errorLog[ctx.guild.id] = ['[{}]   Was reset.'.format(datetime.datetime.now().time().strftime('%H:%M:%S'))]

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

        await ctx.send('Please report any problems you find using `{0}report`'.format(MusicBotConfig.prefix))

    @commands.command()
    async def guilds(self, ctx:commands.context):
        if ctx.author.id == 320837660900065291:
            message = '```'
            for i in self.bot.guilds:
                message += i.name + '  :  ' + i.owner.name + '\n'

        await ctx.send(message + '\n\n\nServer count: {}```'.format(len(self.bot.guilds)))


    @commands.command()
    async def debug(self, ctx:commands.context):

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

                    await ctx.send('Looping: `{}`'.format(self.looping[ctx.channel.guild.id]))

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
                counter = 0

                if self.bot.voice_clients:
                    for i in self.bot.voice_clients:
                        if i.is_playing():
                            counter += 1

                await ctx.send('Voice active in {} servers\nPlaying in {} servers'.format(len(self.bot.voice_clients), counter))

            except:

                pass

    @commands.command()
    async def debugleave(self, ctx:commands.context):
        if ctx.author.id == 320837660900065291:
            guild = await self.bot.fetch_guild(int(ctx.message.content[ctx.message.content.index(' ') + 1:]))

            try:

                guild.voice_client.stop()

            except:

                pass

            try:

                del(queue[guild.id])

            except:

                pass

            try:

                del(video_ids[guild.id])

            except:

                pass
            
            await guild.leave()

    @commands.command()
    async def report(self, ctx:commands.context):

        if (' ') in ctx.message.content:
            if ctx.message.content[ctx.message.content.index(' ') + 1:].replace(' ', '') == '':
                await ctx.message.reply('Error: Empty report')
                return
        else:
            await ctx.message.reply('Error: Empty report')
            return

        #print(os.getcwd())

        os.chdir('..')

        if not os.path.isfile('MusicBot/blacklist_users.txt'.replace('/', os.path.sep)):
            open('blacklist_users.txt', 'w').write('\n')
        if not os.path.isfile('blacklist_servers.txt'):
            open('blacklist_servers.txt', 'w').write('\n')

        file = open('blacklist_users.txt', 'r')
        #print(os.stat('blacklist_users.txt').st_size)
        if os.stat('blacklist_users.txt').st_size > 0:
            for line in file.readlines():
                if line.strip('temp text\n') == str(ctx.author.id):
                    await ctx.send('Unfortunately you have been blacklisted from sending reports')
                    file.close()
                    os.chdir('/MusciBot/Playlists'.replace('/', os.path.sep))
                    return
        file.close()

        file = open('blacklist_servers.txt', 'r')
        if os.stat('blacklist_servers.txt').st_size > 0:
            for line in file.readlines():
                if line.strip('temp text\n') == str(ctx.guild.id):
                    await ctx.send('Unfortunately this server has been blacklisted from sending reports')
                    file.close()
                    os.chdir('/MusciBot/Playlists'.replace('/', os.path.sep))
                    return
        file.close()

        os.chdir('/MusciBot/Playlists'.replace('/', os.path.sep))
        #print(os.getcwd())
        try:
            reportChannel = await self.bot.fetch_channel(MusicBotConfig.reportChannel)
        except:
            pass
        
        try:
            await reportChannel.send('`{0}` reported by `{1}` from server `{2}`\n||{0}|| reported by ||{3}|| from server ||{4}||'.format(ctx.message.content[ctx.message.content.index(' ') + 1:], ctx.author.id, ctx.guild.id, ctx.author, ctx.guild))
        except:
            await ctx.message.reply('Error occurred while reporting problem.')

    @commands.command(aliases=('genres', 'genre'))
    async def _genres(self, ctx:commands.context):
        print(ctx.message.content)
        content = ctx.message.content[ctx.message.content.index(' ') + 1:]
        print(content)
        if re.match(r"https://open.spotify.com/track/(\S{34})", content):
            track = self.spotify.track(track_id=content)
            artist =self.spotify.artist(track["artists"][0]["external_urls"]["spotify"])

            genres = ''

            for i in artist["genres"]:
                genres += i + ', '

            await ctx.message.reply("Artist genres: `{}`\n\n\nSpotify does not reveal song genres currently".format(genres[:-2]))

        elif re.match(r"https://open.spotify.com/artist/(\S{34})", content):
            artist =self.spotify.artist(artist_id=content)

            genres = ''

            for i in artist["genres"]:
                genres += i + ', '

            await ctx.message.reply("Artist genres: `{}`".format(genres[:-2]))

    @commands.command()
    async def shuffle(self, ctx:commands.context):

        server = ctx.message.guild

        if not ctx.author.bot:

            vcMembers = len(server.voice_client.channel.members)

            for i in server.voice_client.channel.members:
                if i.bot:
                    vcMembers -= 1

            if locked.get(ctx.guild.id):
                await ctx.send("Please wait while previous playlist is being added to the queue")
                return

            if len(video_ids[server.id]) < 3:
                await ctx.send('Not enough songs in queue to shuffle')
                return

            if vcMembers > 2:

                if not ctx.author.guild_permissions.administrator:

                    temp = False

                    for i in ctx.author.roles:

                        if i.name.lower() == 'dj':

                            temp = True

                    if not temp:
                        return

        temp = list(zip(queue[server.id], video_ids[server.id][1:]))

        video_ids[server.id] = [video_ids[server.id][0]]

        random.shuffle(temp)

        queue[server.id], temp2 = zip(*temp)

        video_ids[server.id].extend(temp2)

        await ctx.send('Shuffling')
            
    @commands.command(aliases=['leave'])
    async def _leave(self, ctx:commands.context):
        global errorLog

        if not ctx.author.bot:

            if not ctx.author.guild_permissions.administrator:

                temp = False

                for i in ctx.author.roles:

                    if i.name.lower() == 'dj':

                        temp = True

                if not temp:
                    return

            del(errorLog[ctx.guild.id])

            await ctx.message.guild.voice_client.disconnect()



    @commands.command(aliases=['playlistplay', 'listplay'])
    async def _playlistplay(self, ctx:commands.context):
        global serverplaylist

        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        file = open(('{}/{}'.format(str(ctx.channel.guild.id), playlist)).replace('/', os.path.sep), 'r')
        serverplaylist = []
        for line in file.readlines():
            serverplaylist.append(re.findall(r'"id":"{\[(.*?)\]}"', line)[0])

        await self._play(ctx)

    @commands.command(aliases=['playlist', 'list'])
    async def _playlist(self, ctx:commands.context):
        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        file = open(('{}/{}'.format(str(ctx.channel.guild.id)).replace('/', os.path.sep), playlist), 'r')

        lines = file.readlines()

        file.close()

        embedVar = discord.Embed(title="Server playlists", color=0x0e41b5)

        embedVar.description = ''

        for line in lines:

            embedVar.description += re.findall(r'"title":"{\[(.*?)\]}"', line)[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&') + '\n\n'


        await ctx.send(embed=embedVar)

    @commands.command(aliases=['playlists', 'lists'])
    async def _playlists(self, ctx:commands.context):

        if len(os.listdir(str(ctx.channel.guild.id))) == 0:
            
            await ctx.send('No server playlists')

            return
        
        embedVar = discord.Embed(title="Server playlists", color=0x0e41b5)

        embedVar.description = ''

        for file in os.listdir(str(ctx.channel.guild.id)):

            os.chdir(str(ctx.channel.guild.id))

            embedVar.description += file + ', {} songs'.format(len(open(file, 'r').readlines()))

            os.chdir('..')

        await ctx.send(embed=embedVar)

    @commands.command(aliases=['playlistadd', 'listadd'])
    async def _playlistAdd(self, ctx:commands.context):

        if not ctx.author.guild_permissions.administrator:

            temp = False

            for i in ctx.author.roles:

                if i.name.lower() == 'dj':

                    temp = True

            if not temp:
                return

        message = ctx.message.content[ctx.message.content.index(' ') + 1:]

        playlist = message[:message.index(':::')]

        message = urllib.parse.quote_plus(message[message.index(':::') + 3:])

        if not os.path.exists(str(ctx.channel.guild.id)):
            os.mkdir(str(ctx.channel.guild.id))

        if len(os.listdir(str(ctx.channel.guild.id))) >= 20:
            await ctx.send('Maximum number of 20 playlists already reached')

        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + message)
        
        video_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]

        video_name = pafy.new(basic=False, gdata=False, url=video_id).title.replace('\\u0026', '&')

        file = open(('{}/{}'.format(ctx.channel.guild.id, playlist)).replace('/', os.path.sep), "a")

        file.write('"title":"{{[{}]}}", "id":"{{[{}]}}"\n'.format(video_name, video_id))

        file.close()

        await ctx.send('`{}` added to server playlist `{}`'.format(video_name, playlist))



    @commands.command(aliases=['removeplaylist', 'removelist'])
    async def _RemovePlaylist(self, ctx:commands.context):
        if not ctx.author.guild_permissions.administrator:

            temp = False

            for i in ctx.author.roles:

                if i.name.lower() == 'dj':

                    temp = True

            if not temp:
                return

        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        try:        
            os.remove(('{}/{}'.format(ctx.channel.guild.id, playlist)).replace('/', os.path.sep))
        
        except:
            await ctx.send('Playlist `{}` could not be successfully deleted'.format(playlist))
            return

        await ctx.send('Playlist `{}` was successfully deleted'.format(playlist))

    @commands.command(aliases=['playlistremove', 'listremove'])
    async def _playlistRemove(self, ctx:commands.context):

        if not ctx.author.guild_permissions.administrator:

            temp = False

            for i in ctx.author.roles:

                if i.name.lower() == 'dj':

                    temp = True

            if not temp:
                return

        message = ctx.message.content[ctx.message.content.index(' ') + 1:]

        playlist = message[:message.index(' ')]

        message = urllib.parse.quote_plus(message[message.index(' ') + 1:])

        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + message)
        
        video_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]

        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + message)

        video_name = urllib.parse.unquote(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0])

        fileR = open(('{}/{}'.format(ctx.channel.guild.id, playlist)).replace('/', os.path.sep), "r")

        lines = fileR.readlines()

        fileR.close()

        file = open(('{}/{}'.format(ctx.channel.guild.id, playlist)).replace('/', os.path.sep), 'w')

        for line in lines:

            if '"title":"{{[{}]}}", "id":"{{[{}]}}"\n'.format(video_name, video_id) != line:

                file.write(line)



            else:

                await ctx.send('Removed one instance of the song')



                video_name = None
                video_id = None



        file.close()



        if os.stat(('{}/{}'.format(ctx.channel.guild.id, playlist)).replace('/', os.path.sep)).st_size == 0:

            os.remove(('{}/{}'.format(ctx.channel.guild.id, playlist)).replace('/', os.path.sep))





    @commands.command(aliases=['l', 'loop'])
    async def _loop(self, ctx:commands.context):



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

            await ctx.send('No longer looping')



    @commands.command()
    async def pause(self, ctx:commands.context):

        if not ctx.author.bot:



            server = ctx.message.guild



            if server.voice_client.channel != ctx.author.voice.channel:

                return



            server.voice_client.pause()



    @commands.command(aliases=['continue', 'resume'])
    async def _resume(self, ctx:commands.context):

        if not ctx.author.bot:



            server = ctx.message.guild



            if server.voice_client.channel != ctx.author.voice.channel:

                return



            server.voice_client.resume()



    @commands.command(aliases=['q', 'queue'])
    async def _queue(self, ctx:commands.context):

        if queue.get(ctx.channel.guild.id):

            if len(queue[ctx.channel.guild.id]):

                embedVar = discord.Embed(title="Queue", color=0x0e41b5)

                embedVar.description = ''

                for video in queue.get(ctx.channel.guild.id)[1:]:

                    embedVar.description += video[:-8].replace('+', ' ') + '\n'

                await ctx.send(embed=embedVar)



    @commands.command(aliases=['s', 'skip'])
    async def _skip(self, ctx:commands.context):

        if not ctx.author.bot:

            global queue
            global video_ids

            server = ctx.message.guild

            if not video_ids.get(server.id):
                return

            if server.voice_client.channel != ctx.author.voice.channel:

                return

            vcMembers = len(server.voice_client.channel.members)

            for i in server.voice_client.channel.members:
                if i.bot:
                    vcMembers -= 1

            skipMinimum = round((vcMembers / 3) * 2)

            print("Skip minimum: `{}`".format(skipMinimum))
            print("VC members: `{}`".format(vcMembers))
            print((vcMembers / 3) * 2)

            if not self.skipers.get(server.id):
                self.skipers[server.id] = [ctx.message.author.id]

                try:

                    self.skips[server.id] += 1

                except:

                    self.skips[server.id] = 1

            print(self.skipers[server.id])
            if not ctx.message.author.id in self.skipers[server.id]:
                print('test 1')
                self.skipers[server.id].append(ctx.message.author.id)

                try:

                    self.skips[server.id] += 1

                except:

                    self.skips[server.id] = 1

            print(self.skips)

            if self.skips[server.id] >= skipMinimum:

                server.voice_client.stop()

                await ctx.send('Skipping')

                del(self.skips[server.id])

                if len(video_ids[ctx.channel.guild.id]) == 0:

                    del(video_ids[ctx.channel.guild.id])

                    self.playFromList()

                    return



            elif vcMembers <= 2:

                server.voice_client.stop()

                await ctx.send('Skipping')

                del(self.skips[server.id])

                if len(video_ids[ctx.channel.guild.id]) == 0:

                    del(video_ids[ctx.channel.guild.id])

                    self.playFromList()

                    return



            else:

                await ctx.send('`{}` out of `{}` users skipping'.format(self.skips[server.id], skipMinimum))


    
    @commands.cooldown(1.0, MusicBotConfig.cooldown / 5 * 3, commands.BucketType.guild)
    @commands.command(aliases=['fs', 'fskip', 'fastskip', 'forceskip'])
    async def _fskip(self, ctx:commands.context):

        if not ctx.author.bot:

            global queue
            global video_ids

            if not ctx.author.guild_permissions.administrator:

                temp = False

                for i in ctx.author.roles:

                    if i.name.lower() == 'dj':

                        temp = True

                if not temp:
                    return

            server = ctx.message.guild

            server.voice_client.stop()

            await ctx.send('Skipping')

            del(self.skips[server.id])
            
            if queue.get(server.id):
                del(queue[server.id][0])

            if len(queue[server.id]) == 0:

                del(queue[server.id])

            if len(video_ids[ctx.channel.guild.id]) == 0:

                del(video_ids[ctx.channel.guild.id])

                self.playFromList()

                return



    @commands.command(aliases=['r', 'remove'])
    async def _remove(self, ctx:commands.context):

        if not ctx.author.bot:

            global queue
            global video_ids

            if not ctx.author.guild_permissions.administrator:

                temp = False

                for i in ctx.author.roles:

                    if i.name.lower() == 'dj':

                        temp = True

                if not temp:
                    return

            index = int(ctx.message.content[ctx.message.content.index(' ') + 1:])

            server = ctx.message.guild

            if queue.get(server.id):

                del(queue[server.id][index - 1])

            if video_ids.get(server.id):

                del(video_ids[server.id][index - 1])


            if server.voice_client.channel != ctx.author.voice.channel:

                return

            await ctx.send('Removed at `{}`'.format(index))

    @commands.command(aliases=['pn', 'playnow'])
    @commands.cooldown(1.0, MusicBotConfig.cooldown * 2, commands.BucketType.guild)
    async def _playnow(self, ctx:commands.context):

        server = ctx.message.guild

        if len(video_ids[server.id]) < 2:
            await ctx.send('Not enough songs in queue to use that command')
            return

        await ctx.send(ctx.message.content)

        ctx.message.content = MusicBotConfig.prefix + 'p' + ctx.message.content[4:]

        await ctx.send(ctx.message.content)

        await self._play(ctx)

        server.voice_client.stop()

        try:
            del(self.skips[server.id])

        except:
            pass

        if len(video_ids[server.id]) == 0:

            del(video_ids[server.id])

            #return

        queue[server.id].insert(0, queue[server.id][len(queue[server.id]) - 1])

        del(queue[server.id][len(queue[server.id]) - 1])

        video_ids[server.id].insert(0, video_ids[server.id][len(video_ids[server.id]) - 1])

        del(video_ids[server.id][len(video_ids[server.id]) - 1])

        await self.playFromList()

    def formatDuration(self, durationIn): # Move??
        duration = durationIn
        seconds = str(duration % 60)
        if (len(seconds) == 1):
            seconds = "0" + seconds

        duration = int((duration - (duration % 60)) / 60)
        minutes = str(duration % 60)
        if (len(minutes) == 1):
            minutes = "0" + minutes

        duration = int((duration - (duration % 60)) / 60)
        hours = str(duration)
        if (len(hours) == 1):
            hours = "0" + hours

        return hours + ":" + minutes + ":" + seconds

    @commands.command(aliases=['p', 'play'])
    @commands.cooldown(1.0, MusicBotConfig.cooldown, commands.BucketType.guild)
    async def _play(self, ctx:commands.context):


        global serverplaylist
        global queue
        global video_ids
        global locked
        global searchterms 
        global errorLog

        if not ctx.author.bot:

            if ctx.author.voice == None:

                await ctx.send('You are not in a voice channel')

                return



            server = ctx.message.guild

            voice_channel = server.voice_client

            channel = ctx.author.voice.channel

            name = urllib.parse.quote_plus(ctx.message.content[ctx.message.content.index(' ') + 1:])

            if locked.get(ctx.guild.id):
                await ctx.send("Please wait while previous playlist is being added to the queue")
                return
                
            

            if name == '':

                await ctx.send('You must specify the name of the video')

                return



            if server.voice_client == None:

                await channel.connect()

                voice_channel = server.voice_client

                errorLog[ctx.guild.id] = ['[{}]   Joined VC.'.format(datetime.datetime.now().time().strftime('%H:%M:%S'))]


            elif not server.voice_client.is_connected():

                await channel.connect()

                voice_channel = server.voice_client

                errorLog[ctx.guild.id] = ['[{}]   Joined VC.'.format(datetime.datetime.now().time().strftime('%H:%M:%S'))]



            if server.voice_client.channel != ctx.author.voice.channel:



                if len(server.voice_client.channel.members) > 1:

                    await ctx.send('You have to be in the same voice channel')

                    return

                else:

                    await server.voice_client.disconnect()

                    try:

                        del(queue[ctx.channel.guild.id])

                    except:

                        pass

                    try:

                        del(video_ids[ctx.channel.guild.id])

                    except:

                        pass

                    await channel.connect()

                    errorLog[ctx.guild.id] = ['[{}]   Joined VC.'.format(datetime.datetime.now().time().strftime('%H:%M:%S'))]

            if not queue.get(server.id):
                queue[server.id] = []
            if not video_ids.get(server.id):
                video_ids[server.id] = []

            #///////////////////////////Spotify
            if re.match(r"https://open.spotify.com/track/(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):
                
                try:
                    searchterms[server.id] = self.spotify_to_youtube(ctx.message.content[ctx.message.content.index(' ') + 1:], 2)

                except:

                    await ctx.send('Invalid link')

                name = urllib.parse.quote_plus(searchterms[server.id][0])
            #///////////////////////////



            #///////////////////////////Spotify playlists
            if re.match(r"https://open.spotify.com/playlist/(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):
                try:
                    searchterms[server.id] = self.spotify_to_youtube(ctx.message.content[ctx.message.content.index(' ') + 1:], 1)

                    if queue.get(ctx.guild.id):
                        if len(queue[ctx.guild.id]) + len(searchterms[server.id]) >= maxSize:
                            await ctx.send('Maximum queue size reached')

                            searchterms[server.id] = searchterms[server.id][:maxSize - len(queue[ctx.guild.id])]

                    else:
                        if len(searchterms[server.id]) >= maxSize:
                            await ctx.send('Maximum queue size reached')

                            searchterms[server.id] = searchterms[server.id][:maxSize]
                except:

                    await ctx.send('Invalid link')

                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(searchterms[server.id][0]))

                try:

                    video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                except:

                    video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]
                    
                song = pafy.new(basic=False, gdata=False, url=video_ids[server.id][len(video_ids[server.id]) - 1])

                try:

                    queue[server.id].append(song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&') + datetime.datetime.now().time().strftime('%H:%M:%S'))

                except:

                    queue[server.id] = [song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&')]

                searchterms[server.id] = searchterms[server.id][1:]

                locked[server.id] = True
                thread = Thread(target = self.add_to_queue, args = (searchterms, server, ctx))
                thread.start()
            #///////////////////////////



            #///////////////////////////Youtube playlists
            elif (re.match(r"https://www.youtube.com/playlist\?list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://youtube.com/playlist\?list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://www.youtube.com/watch\?v=(\S{11})&list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://youtube.com/watch\?v=(\S{11})&list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:])) and not (re.match(r"https://youtube.com/watch\?v=(\S{11})&list=(.*?)&index=(.*?)", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://www.youtube.com/watch\?v=(\S{11})&list=(.*?)&index=(.*?)", ctx.message.content[ctx.message.content.index(' ') + 1:])):
                
                #print(ctx.message.content[ctx.message.content.index(' ') + 1:])
                #print("Test: {}".format(re.match(r"https://www.youtube.com/watch\?v=(\S{11})&list=(.*?)&index=(.*?)", ctx.message.content[ctx.message.content.index(' ') + 1:])))

                ctx.message.content = re.sub(r'watch\?v=(\S{11})&', "playlist?", ctx.message.content)[4:]

                #print(ctx.message.content)

                playlist = pafy.get_playlist2(ctx.message.content)

                searchterms[server.id] = []

                for i in playlist:
                    searchterms[server.id].append(i.videoid)

                locked[server.id] = True

                print(searchterms)
                    
                song = pafy.new(basic=False, gdata=False, url=searchterms[server.id][0])

                try:

                    queue[server.id].append(song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&') + datetime.datetime.now().time().strftime('%H:%M:%S'))

                except:

                    queue[server.id] = [song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&')]

                print(queue)

                try:

                    video_ids[server.id].append(searchterms[server.id][0])

                except:

                    video_ids[server.id] = [searchterms[server.id][0]]

                searchterms[server.id] = searchterms[server.id][1:]

                print(searchterms)

                thread = Thread(target = self.add_to_queue, args = (searchterms, server, ctx))
                thread.start()  
            #///////////////////////////



            elif serverplaylist is not None:
                
                server = ctx.message.guild

                voice_channel = server.voice_client

                channel = ctx.author.voice.channel



                name = urllib.parse.quote_plus(ctx.message.content[ctx.message.content.index(' ') + 1:])



                if server.voice_client == None:

                    await channel.connect()

                    voice_channel = server.voice_client

                    errorLog[ctx.guild.id] = ['[{}]   Joined VC.'.format(datetime.datetime.now().time().strftime('%H:%M:%S'))]



                elif not server.voice_client.is_connected():

                    await channel.connect()

                    voice_channel = server.voice_client

                    errorLog[ctx.guild.id] = ['[{}]   Joined VC.'.format(datetime.datetime.now().time().strftime('%H:%M:%S'))]



                if server.voice_client.channel != ctx.author.voice.channel:



                    if len(server.voice_client.channel.members) > 1:

                        await ctx.send('You have to be in the same voice channel')

                        return

                    else:

                        await server.voice_client.disconnect()

                        try:

                            del(queue[ctx.channel.guild.id])

                        except:

                            pass

                        try:

                            del(video_ids[ctx.channel.guild.id])

                        except:

                            pass

                        await channel.connect()



                for i in serverplaylist:

                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)

                    try:

                        video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                    except:

                        video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]
                        
                    song = pafy.new(basic=False, gdata=False, url=video_ids[server.id][len(video_ids[server.id]) - 1])

                    try:

                        queue[server.id].append(song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&'))

                    except:

                        queue[server.id] = [song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&')]

                    queue[server.id][len(queue[server.id]) - 1] += '   **Duration: {}**'.format(song.duration) +  + datetime.datetime.now().time().strftime('%H:%M:%S')

                serverplaylist = None
                    

            else:
                if queue.get(ctx.guild.id): #//START

                    if len(queue[ctx.guild.id]) >= maxSize:
                        await ctx.send('Maximum queue size reached')

                    elif queue.get(serverplaylist):
                        if len(queue[ctx.guild.id]) + len(serverplaylist) >= maxSize:
                            await ctx.send('Maximum queue size reached')

                            serverplaylist = serverplaylist[:len(queue[ctx.guild.id]) - len(serverplaylist)] #//////FOR LATER
                    
                        elif len(serverplaylist) >= maxSize:
                            await ctx.send('Maximum queue size reached')

                            serverplaylist = serverplaylist[:maxSize] #//END

                print(ctx.message.content)

                ctx.message.content = re.sub(r"&list=(\S{34})&index=(.*?)", "", ctx.message.content)

                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + name)
                
                try:

                    video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                except:

                    video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]

                with yt_dlp.YoutubeDL({"format": "bestaudio"}) as ytdl:
                    song:dict = ytdl.extract_info(video_ids[server.id][len(video_ids[server.id]) - 1], download=False) 

                try:

                    queue[server.id].append(song["title"].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&'))

                except:

                    queue[server.id] = [song["title"].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&')]
                
                queue[server.id][len(queue[server.id]) - 1] += '   **Duration: {}**'.format(self.formatDuration(song["duration"])) + datetime.datetime.now().time().strftime('%H:%M:%S')

            with yt_dlp.YoutubeDL({"format": "bestaudio"}) as ytdl:
                song:dict = ytdl.extract_info(video_ids[server.id][0], download=False) 

                print(f"URL: \"{video_ids[server.id][0]}\"")
                print(f"Audio URL: \"{song['url']}\"")
                print(f"Duration: {self.formatDuration(song['duration'])}")

                if not errorLog[ctx.guild.id][0]:
                    errorLog[ctx.guild.id] = ['[{}]   Used in VC despite no recorded connection'.format(datetime.datetime.now().time().strftime('%H:%M:%S'))]

                errorLog[ctx.guild.id][0] += '\n\n[{}]   Added to queue: `{}`'.format(datetime.datetime.now().time(), queue[server.id][len(queue[server.id]) - 1])

                if not voice_channel.is_playing():

                    voice_channel.play(discord.FFmpegPCMAudio(song["url"], **self.ffmpegPCM_options), after=lambda e: self.stop_playing(server))
                    
                    await ctx.send('Now playing: `{}`'.format(re.sub(r'   \*\*Duration: .*', "", queue[server.id][0]).replace('\\', '')))

                    if queue.get(server.id):
                        if len(queue[ctx.guild.id]) >= maxSize:
                            await ctx.send('Maximum queue size reached')

                            queue = queue[:maxSize]

                else:
                    print((queue[server.id][len(queue[server.id]) - 1]).replace('\\', ''))
                    await ctx.send('Added to queue: `{}`'.format(re.sub(r'   \*\*Duration: .*', "", queue[server.id][len(queue[server.id]) - 1]).replace('\\', '')))

    @_play.error
    async def _play_error(self, ctx:commands.context, error):
        print(f"//////{error}//////")
        print(type(error))
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('{0}play is on cooldown to avoid slowing down bot'.format(MusicBotConfig.prefix))

        elif isinstance(error, commands.CommandInvokeError): #str(error) == 'Command raised an exception: OSError: ERROR: Sign in to confirm your age\nThis video may be inappropriate for some users.':
            
            await ctx.send('You may have tried playing an age restricted video, Jazzy is currently not able to play age restricted videos due to restrictions by YouTube. Error code: 03')
            
            try:
                del(video_ids[ctx.guild.id][len(video_ids[ctx.guild.id]) - 1])
            except:
                pass
            pass

    @_fskip.error
    async def _fskip_error(self, ctx:commands.context, error):
        if isinstance(error, commands.CommandOnCooldown):
            pass
            #await ctx.send('{0}play is on cooldown to avoid slowing down bot'.format(MusicBotConfig.prefix))

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        global errorLog
        print('LogFile-{}.txt'.format(interaction.guild.name))
        if interaction.custom_id == 'error_log':
            try:
                reportChannel = await self.bot.fetch_channel(MusicBotConfig.reportChannel)

                os.chdir('..')

                log = open('LogFile-{}.txt'.format(interaction.guild.name), 'w')
                log.write(errorLog[interaction.guild.id][0])
                log.close()

                try:
                    await reportChannel.send(file=discord.File('LogFile-{}.txt'.format(interaction.guild.name)))
                except:
                    pass

                os.remove('LogFile-{}.txt'.format(interaction.guild.name))

                os.chdir('/MusciBot/Playlists'.replace('/', os.path.sep))

                await interaction.message.delete()
            except:
                pass



    @commands.command()
    async def soundcloud(self, ctx:commands.context):
        await ctx.message.reply("Not implemented yet.")
        print('sex')

    

async def setup(bot: commands.Bot):
    await bot.add_cog(MainCog(bot))