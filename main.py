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
for key in ['TOKEN', 'GUILD_ID', 'CHANNEL_ID', 'PREFIX', 'FFMPEG_PATH']:
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


async def play_or_resume(prev_err=None):
    source = await discord.FFmpegOpusAudio.from_probe(os.path.join('music', cur_file))
    # print(source.volume)
    # source.volume = 1
    vc.play(source)
    logging.info(f'Request to play music: playing music/{cur_file} from file"')


@bot.event
async def on_ready():
    global vc
    logging.info(f'Logged in as {bot.user.name}')
    if guild := find(lambda g: str(g.id) == os.getenv('GUILD_ID'), bot.guilds):
        logging.info(f'Found guild {guild.name} (id: {guild.id})')
        if channel := find(lambda c: str(c.id) == os.getenv('CHANNEL_ID'), guild.voice_channels):
            logging.info(f'Found channel {channel.name} (id: {channel.id})')
            try:
                vc = await channel.connect()
                await play_or_resume()
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
    if not before.channel and after.channel:  # Joined
        if len(after.channel.members) == 2:
            logging.info(f'User join (first user)')
            await play_or_resume()
    elif before.channel and not after.channel:  # Left
        if len(before.channel.members) == 1 and vc.is_playing():
            logging.info(f'User leave (last user)')
            vc.pause()


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
    pass


@bot.command(
    name='download',
    help='Download a new version of plastic love (Youtube links only)'
)
async def _command_download(ctx, link, file_name):
    pass


@bot.command(
    name='remove',
    help='Remove a version of plastic love'
)
async def _command_download(ctx, file_name):
    await ctx.send('No!')  # No


bot.run(os.getenv('TOKEN'))
