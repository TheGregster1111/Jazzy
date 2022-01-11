from typing import Counter
import discord
from discord.enums import MessageType
from discord.ext.commands import errors
import discord.member
import discord.channel
import discord.message
import discord.voice_client
from discord.ext import commands, tasks
from discord_components import Button, ButtonStyle
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

#regex dictionary
#(.*?)    match unspecified length of characters
#(?:.*?)    ignore unspecified length of characters

print('Test file successfully run')

class MainCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.playFromList.start()
        self.clear.start()

        for filename in os.listdir(os.path.dirname(__file__) + '/Music_Cogs'):

            if filename.endswith('.py'):

                self.bot.load_extension(f'Music_Cogs.{filename[:-3]}')

        try:
            os.chdir('source/repos/MusicBot')
        except:
            pass

        os.chdir('Playlists')

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
    
    maxSize = 60

    ffmpegPCM_options = {

        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 1000",

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

            results = self.spotify.track(track_id=URL)

            trackList = [results["name"] + " - " + results["artists"][0]["name"]]

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

        

        self.playFromList()
    

    def add_to_queue(self, searchterms, server, ctx):

        global video_ids
        global queue

        counter = 0

        for i in searchterms[server.id]:

            counter += 1

            i = urllib.parse.quote_plus(i)

            html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + i)

            try:

                queue[server.id].append(re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', html.read().decode())[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&'))

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

        os.rmdir(str(guild.id))

        os.chdir('..')



    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(error)

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.channel.id == 922764743540895775 and not ctx.author.bot:
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


    @tasks.loop(seconds=5)
    async def playFromList(self):

        global queue
        global video_ids

        for i in self.bot.voice_clients:

            if not i.is_playing() and video_ids.get(i.guild.id):

                song = pafy.new(basic=False, gdata=False, url=video_ids[i.guild.id][0])



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

        embedVar.add_field(name='{0}play {0}p'.format(MusicBotConfig.prefix), value='Play the audio of a youtube song, playlist, or spotify playlist'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}playnow {0}pn'.format(MusicBotConfig.prefix), value='Same as {0}play but plays the song instantly'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}skip {0}s'.format(MusicBotConfig.prefix), value='Skip current song'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}fs {0}fskip {0}fastskip {0}forceskip'.format(MusicBotConfig.prefix), value='Instantly skip current song, only useable by someone with a role named DJ or an admin'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}queue {0}q'.format(MusicBotConfig.prefix), value='View the current queue'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}remove {0}r'.format(MusicBotConfig.prefix), value='Remove the specified song from the queue, example: {0}remove 2'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}reset'.format(MusicBotConfig.prefix), value='Reset the bot if it is malfunctioning'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}pause'.format(MusicBotConfig.prefix), value='Pause the song'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}continue {0}resume'.format(MusicBotConfig.prefix), value='Resume the song'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}loop'.format(MusicBotConfig.prefix), value='Starts or stops looping the song'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}leave'.format(MusicBotConfig.prefix), value='Makes the bot leave the voice chat'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}shuffle'.format(MusicBotConfig.prefix), value='Shuffles the queue'.format(MusicBotConfig.prefix), inline=False)
        
        embedVar.add_field(name='{0}playlistplay {0}listplay'.format(MusicBotConfig.prefix), value='Use "{0}listplay `Playlist name`" to play songs from a server playlist'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}playlistadd {0}listadd'.format(MusicBotConfig.prefix), value='Use "{0}listadd `Playlist name`:::`Song name`" to add a song to a server playlist'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}playlistremove {0}listremove'.format(MusicBotConfig.prefix), value='Use "{0}listremove `Playlist name`:::`Song name`" to remove a song from a server playlist'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}removeplaylist {0}removelist'.format(MusicBotConfig.prefix), value='Use "{0}removelist `Playlist name`" to remove a server playlist'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}playlists {0}lists'.format(MusicBotConfig.prefix), value='View all server playlists'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='{0}playlist {0}list'.format(MusicBotConfig.prefix), value='Use "{0}list `Playlist name`" to view all songs in specified playlist'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='Extra stuff'.format(MusicBotConfig.prefix), value='Try making a new voice channel named "Create VC" and connecting to it'.format(MusicBotConfig.prefix), inline=False)

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
    async def guilds(self, ctx):
        if ctx.author.id == 320837660900065291:
            message = '```'
            for i in self.bot.guilds:
                message += i.name + '  :  ' + i.owner.name + '\n'

        await ctx.send(message + '\n\n\nServer count: {}```'.format(len(self.bot.guilds)))


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
    async def debugleave(self, ctx):
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
    async def report(self, ctx):

        print(os.getcwd())

        os.chdir('..')

        if not os.path.isfile('MusicBot/blacklist_users.txt'):
            open('blacklist_users.txt', 'w').write('\n')
        if not os.path.isfile('blacklist_servers.txt'):
            open('blacklist_servers.txt', 'w').write('\n')

        file = open('blacklist_users.txt', 'r')
        print(os.stat('blacklist_users.txt').st_size)
        if os.stat('blacklist_users.txt').st_size > 0:
            for line in file.readlines():
                if line.strip('temp text\n') == str(ctx.author.id):
                    await ctx.send('Unfortunately you have been blacklisted from sending reports')
                    file.close()
                    os.chdir('Playlists')
                    return
        file.close()

        file = open('blacklist_servers.txt', 'r')
        if os.stat('blacklist_servers.txt').st_size > 0:
            for line in file.readlines():
                if line.strip('temp text\n') == str(ctx.guild.id):
                    await ctx.send('Unfortunately this server has been blacklisted from sending reports')
                    file.close()
                    os.chdir('Playlists')
                    return
        file.close()

        os.chdir('Playlists')
        print(os.getcwd())
        try:
            reportChannel = await self.bot.fetch_channel(922764743540895775)
        except:
            pass
        
        try:
            await reportChannel.send('`{0}` reported by `{1}` from server `{2}`\n||{0}|| reported by ||{3}|| from server ||{4}||'.format(ctx.message.content[ctx.message.content.index(' ') + 1:], ctx.author.id, ctx.guild.id, ctx.author, ctx.guild))
        except:
            await ctx.send('Error occurred while reporting problem')

    @commands.command()
    async def shuffle(self, ctx):

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
    async def _leave(self, ctx):

        if not ctx.author.bot:

            if not ctx.author.guild_permissions.administrator:

                temp = False

                for i in ctx.author.roles:

                    if i.name.lower() == 'dj':

                        temp = True

                if not temp:
                    return



            await ctx.message.guild.voice_client.disconnect()



    @commands.command(aliases=['playlistplay', 'listplay'])
    async def _playlistplay(self, ctx):
        global serverplaylist

        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        file = open('{}/{}'.format(str(ctx.channel.guild.id), playlist), 'r')
        serverplaylist = []
        for line in file.readlines():
            serverplaylist.append(re.findall(r'"id":"{\[(.*?)\]}"', line)[0])

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

            embedVar.description += re.findall(r'"title":"{\[(.*?)\]}"', line)[0].replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&') + '\n\n'


        await ctx.send(embed=embedVar)

    @commands.command(aliases=['playlists', 'lists'])
    async def _playlists(self, ctx):

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
    async def _playlistAdd(self, ctx):

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

        file = open('{}/{}'.format(ctx.channel.guild.id, playlist), "a")

        file.write('"title":"{{[{}]}}", "id":"{{[{}]}}"\n'.format(video_name, video_id))

        file.close()

        await ctx.send('`{}` added to server playlist `{}`'.format(video_name, playlist))



    @commands.command(aliases=['removeplaylist', 'removelist'])
    async def _RemovePlaylist(self, ctx):
        if not ctx.author.guild_permissions.administrator:

            temp = False

            for i in ctx.author.roles:

                if i.name.lower() == 'dj':

                    temp = True

            if not temp:
                return

        playlist = ctx.message.content[ctx.message.content.index(' ') + 1:]

        try:        
            os.remove('{}/{}'.format(ctx.channel.guild.id, playlist))
        
        except:
            await ctx.send('Playlist `{}` could not be successfully deleted'.format(playlist))
            return

        await ctx.send('Playlist `{}` was successfully deleted'.format(playlist))

    @commands.command(aliases=['playlistremove', 'listremove'])
    async def _playlistRemove(self, ctx):

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

        fileR = open('{}/{}'.format(ctx.channel.guild.id, playlist), "r")

        lines = fileR.readlines()

        fileR.close()

        file = open('{}/{}'.format(ctx.channel.guild.id, playlist), 'w')

        for line in lines:

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

            await ctx.send('No longer looping')



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


    
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    @commands.command(aliases=['fs', 'fskip', 'fastskip', 'forceskip'])
    async def _fskip(self, ctx):

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

            if len(video_ids[ctx.channel.guild.id]) == 0:

                del(video_ids[ctx.channel.guild.id])

                self.playFromList()

                return



    @commands.command(aliases=['r', 'remove'])
    async def _remove(self, ctx):

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
    @commands.cooldown(1.0, 10.0, commands.BucketType.guild)
    async def _playnow(self, ctx):

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

    @commands.command(aliases=['p', 'play'])
    @commands.cooldown(1.0, 5.0, commands.BucketType.guild)
    async def _play(self, ctx):

        global serverplaylist
        global queue
        global video_ids
        global locked
        global searchterms 

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

            if not queue.get(server.id):
                queue[server.id] = []
            if not video_ids.get(server.id):
                video_ids[server.id] = []

            if re.match(r"https://open.spotify.com/track/(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]):
                
                try:
                    searchterms[server.id] = self.spotify_to_youtube(ctx.message.content[ctx.message.content.index(' ') + 1:], 2)

                except:

                    await ctx.send('Invalid link')

                name = urllib.parse.quote_plus(searchterms[server.id][0])

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

                


                html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(searchterms[server.id][0]))

                try:

                    video_ids[server.id].append(re.findall(r"watch\?v=(\S{11})", html.read().decode())[0])

                except:

                    video_ids[server.id] = [re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]]
                    
                song = pafy.new(basic=False, gdata=False, url=video_ids[server.id][len(video_ids[server.id]) - 1])

                try:

                    queue[server.id].append(song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&'))

                except:

                    queue[server.id] = [song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&')]

                searchterms[server.id] = searchterms[server.id][1:]

                locked[server.id] = True
                thread = Thread(target = self.add_to_queue, args = (searchterms, server, ctx))
                thread.start()



            #///////////////////////////Playlists below



            elif (re.match(r"https://www.youtube.com/playlist\?list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://youtube.com/playlist\?list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://www.youtube.com/watch\?v=(\S{11})&list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://youtube.com/watch\?v=(\S{11})&list=(\S{34})", ctx.message.content[ctx.message.content.index(' ') + 1:])) and not (re.match(r"https://youtube.com/watch\?v=(\S{11})&list=(.*?)&index=(.*?)", ctx.message.content[ctx.message.content.index(' ') + 1:]) or re.match(r"https://www.youtube.com/watch\?v=(\S{11})&list=(.*?)&index=(.*?)", ctx.message.content[ctx.message.content.index(' ') + 1:])):
                
                #print(ctx.message.content[ctx.message.content.index(' ') + 1:])
                #print("Test: {}".format(re.match(r"https://www.youtube.com/watch\?v=(\S{11})&list=(.*?)&index=(.*?)", ctx.message.content[ctx.message.content.index(' ') + 1:])))

                ctx.message.content = re.sub(r'watch\?v=(\S{11})&', "playlist?", ctx.message.content)[4:]

                locked[server.id] = True

                html = urllib.request.urlopen(ctx.message.content)

                searchterms[server.id] = re.findall(r"watch\?v=(\S{11})", html.read().decode())

                print(searchterms)
                    
                song = pafy.new(basic=False, gdata=False, url=searchterms[server.id][0])

                try:

                    queue[server.id].append(song.title.replace('|', '\|').replace('*', '\*').replace('~', '\~').replace('_', '\_').replace('\\u0026', '&'))

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

                    queue[server.id][len(queue[server.id]) - 1] += '   **Duration: {}**'.format(song.duration)

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

                ctx.message.content = re.sub(r"&list=(\S{34})&index=(.*?)", "", ctx.message.content)

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
                
                queue[server.id][len(queue[server.id]) - 1] += '   **Duration: {}**'.format(song.duration)



            try:
                song = pafy.new(basic=False, gdata=False, url=video_ids[server.id][0])

            except OSError as e:
                print("{}    aaaaaaa".format(e))

            audio = song.getbestaudio()

            #print('Audio URL: "{}"'.format(audio.url))

            if not voice_channel.is_playing():

                voice_channel.play(discord.FFmpegPCMAudio(audio.url, **self.ffmpegPCM_options), after=lambda e: self.stop_playing(server))
                
                await ctx.send('Now playing: `{}`'.format(re.sub(r'   \*\*Duration: (.*?)\*\*', "", queue[server.id][0]).replace('\\', '')))
                
                del(queue[server.id][0])
                
                if len(queue[server.id]) == 0:

                    del(queue[server.id])

                if queue.get(server.id):
                    if len(queue[ctx.guild.id]) >= maxSize:
                        await ctx.send('Maximum queue size reached')

                        queue = queue[:maxSize]

            else:
                await ctx.send('Added to queue: `{}`'.format(re.sub(r'   \*\*Duration: (.*?)\*\*', "", queue[server.id][len(queue[server.id]) - 1]).replace('\\', '')))

    @_play.error
    async def _play_error(self, ctx, error):
        print('//\\\\{}//\\\\'.format(error))
        print(type(error))
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('{0}play is on cooldown to avoid slowing down bot'.format(MusicBotConfig.prefix))

        elif isinstance(error, commands.CommandInvokeError): #str(error) == 'Command raised an exception: OSError: ERROR: Sign in to confirm your age\nThis video may be inappropriate for some users.':
            
            await ctx.send('You may have tried playing an age restricted video, Jazzy is currently not able to play age restricted videos due to restrictions by YouTube')
            
            try:
                del(video_ids[ctx.guild.id][len(video_ids[ctx.guild.id]) - 1])
            except:
                pass
            pass

    @_fskip.error
    async def _fskip_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            pass
            #await ctx.send('{0}play is on cooldown to avoid slowing down bot'.format(MusicBotConfig.prefix))

    @commands.command()
    async def soundcloud(self, ctx):
        print('sex')

    

def setup(bot):
    bot.add_cog(MainCog(bot))

