import subprocess as sub
import discord
from discord.utils import find
import logging
import coloredlogs
import colorama
from discord.ext import commands
from dotenv import load_dotenv
import os
import sys

# Init Printing
LOG_FORMAT = '[%(asctime)s/%(name)s] %(levelname)s %(message)s'
TIME_FORMAT = '%H:%M:%S'

colorama.init()
coloredlogs.install(fmt=LOG_FORMAT, datefmt=TIME_FORMAT)

# Check Config
load_dotenv()
logging.info('Checking env for configuration options...')
for key in ['TOKEN', 'GUILD_ID', 'CHANNEL_ID', 'PREFIX']:
    if key not in os.environ:
        logging.error(f'env missing option {key}!')
        sys.exit(-1)

# Discord Init
try:
    import ctypes
    discord.opus.load_opus(ctypes.util.find_library('opus'))
except Exception as e:
    print(type(e), str(e))

bot = commands.Bot(os.getenv('PREFIX'))
cur_file = 'plastic-lover.mp3'
vc = None


def die(msg):
    logging.error(msg)
    sys.exit(-1)


async def check_play():
    user_cnt = sum(map(lambda m: int(not m.bot), vc.channel.members))

    logging.info('Checking current play state...')
    if user_cnt == 0:
        if vc.is_playing():
            vc.pause()
            logging.info('Channel now empty, pausing song...')
    else:
        if vc.is_paused():
            vc.resume()
            logging.info('Channel no longer empty, resuming song...')
        else:
            source = await discord.FFmpegOpusAudio.from_probe(os.path.join('music', cur_file))
            vc.play(source, after=check_play)
            logging.info(f'Channel no longer empty, starting music/{cur_file} from file"')


@bot.event
async def on_ready():
    global vc
    logging.info(f'Logged in as {bot.user.name}')

    await bot.change_presence(activity=discord.Game(name='Plastic Love'))
    if guild := find(lambda g: str(g.id) == os.getenv('GUILD_ID'), bot.guilds):
        logging.info(f'Found guild {guild.name} (id: {guild.id})')
        if channel := find(lambda c: str(c.id) == os.getenv('CHANNEL_ID'), guild.voice_channels):
            logging.info(f'Found channel {channel.name} (id: {channel.id})')
            try:
                vc = await channel.connect()
                await check_play()
                logging.info('Joined voice channel')
            except Exception as e:
                die(f'Error occured while joining voice channel: {type(e)}: {e}')
        else:
            die(f'Could not find channel with id {os.getenv("CHANNEL_ID")} (only found (voice) channels {list(map(lambda x: x.name, guild.voice_channels))})')
    else:
        die(f'Could not find guild with id {os.getenv("GUILD_ID")} (only found guilds {list(map(lambda x: x.name, bot.guilds))})')


@bot.event
async def on_voice_state_update(user, before, after):
    if user.bot:
        return
    logging.info(f'Voice channel status change')
    await check_play()


# Commands
@bot.command(
    name='list',
    help='List current'
)
async def _command_list(ctx):
    fmt = '\n'.join(os.listdir('music'))
    await ctx.send(f'**Currently downloaded versions of Plastic Love:**\n{fmt}')


@bot.command(
    name='select',
    help='Select a different version of plastic love'
)
async def _command_select(ctx, file):
    global cur_file
    fs = os.listdir('music')
    file = file.strip()
    if file not in fs:
        await ctx.send(f'File {file} does not exist!')
    else:
        cur_file = file
        if vc.is_playing() or vc.is_paused():
            vc.stop()
        await check_play()


@bot.command(
    name='download',
    help='Download a new version of plastic love (Youtube links only)'
)
async def _command_download(ctx, link, file_name):
    GREEN = 0x008E44
    RED = 0xA62019

    async with ctx.channel.typing():
        res = sub.run(['youtube-dl', '--extract-audio', '--audio-format', 'mp3', '--output', 'music/' + file_name, link],
                      text=True, stdout=sub.PIPE, stderr=sub.PIPE)
        await ctx.send(embed=discord.Embed(title='Download Info', color=RED if res.returncode else GREEN)
                       .add_field(name='Process Output', value=res.stdout or 'N/A', inline=False)
                       .add_field(name='Process Errors', value=res.stderr or 'N/A', inline=False)
                       .add_field(name='Exit Code', value=str(res.returncode)))


@bot.command(
    name='remove',
    help='Remove a version of plastic love'
)
async def _command_remove(ctx, file_name):
    await ctx.send('No!')  # No


bot.run(os.getenv('TOKEN'))
