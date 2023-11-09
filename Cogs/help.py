import discord
from discord.enums import MessageType
from discord.ext import commands, tasks
from discord.ui.button import Button
import MusicBotConfig

class Cog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx:commands.context):

        embedVar = discord.Embed(title="Commands", color=0x0e41b5)

        embedVar.add_field(name='{0}play {0}p'.format(MusicBotConfig.prefix), value='Play the audio of a youtube song, playlist, or spotify playlist'.format(MusicBotConfig.prefix), inline=False)

        #embedVar.add_field(name='{0}playnow {0}pn'.format(MusicBotConfig.prefix), value='Same as {0}play but plays the song instantly'.format(MusicBotConfig.prefix), inline=False)

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

        embedVar.add_field(name='{0}genres {0}genre'.format(MusicBotConfig.prefix), value='Use "{0}genres `Spotify link to either artist or song`" to get a list of artist genres'.format(MusicBotConfig.prefix), inline=False)

        embedVar.add_field(name='Extra stuff'.format(MusicBotConfig.prefix), value='Try making a new voice channel named "Create VC" and connecting to it'.format(MusicBotConfig.prefix), inline=False)

        await ctx.send(
            content = None,
            embed = embedVar,
            view=discord.ui.View().add_item(
            
                Button(
                    label = "Discord",
                    style = discord.ButtonStyle.url,
                    url = 'https://discord.gg/qpP4CZABJx'
                )

            ).add_item(

                Button(
                    label = "Invite",
                    style = discord.ButtonStyle.url,
                    url = 'https://discord.com/api/oauth2/authorize?client_id=887684182975840296&permissions=0&scope=bot'
                )

            ).add_item(

                Button(
                    label = "Website",
                    style = discord.ButtonStyle.url,
                    url = 'https://trim-keep-354608.ew.r.appspot.com/'
                )
            
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Cog(bot))