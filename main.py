import os
import discord
import requests
import asyncio
from discord import app_commands

from myserver import server_on

# Discord Bot Token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Twitch API Credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TWITCH_USERNAME = 'Uranutsu'

# URLs for Twitch API
OAUTH_URL = 'https://id.twitch.tv/oauth2/token'
USER_INFO_URL = 'https://api.twitch.tv/helix/users'
STREAMS_URL = 'https://api.twitch.tv/helix/streams'

# Intents for Discord bot
intents = discord.Intents.default()
intents.message_content = True

# สร้าง Client สำหรับ Discord
client = discord.Client(intents=intents)

# สร้าง tree สำหรับ Slash Commands
tree = app_commands.CommandTree(client)

@tree.command(name="twitch", description="Check if the Twitch user is live")
async def twitch(interaction: discord.Interaction):
    token = get_twitch_token()
    user_id, icon_url = get_user_id(TWITCH_USERNAME, token)
    stream = check_live_status(user_id, token)

    if stream:
        embed = discord.Embed(
            title=f'{TWITCH_USERNAME} is live on Twitch!',
            description=f'Watch here: https://twitch.tv/{TWITCH_USERNAME}',
            color=0x9146FF
        )
        embed.set_thumbnail(url=icon_url)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f'{TWITCH_USERNAME} is not live on Twitch.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!rule'):
        rules = (
            "✨   กฎการอยู่ร่วมกัน    👑:\n\n"
            "⚝ พูดคุยกันอย่างสุภาพให้เกียรติซึ่งกันและกัน\n\n"
            "⚝ ไม่ซีเรียสเรื่องคำหยาบใช้คำหยาบได้ แต่ขอให้อยู่ในขอบเขตพองามและเหมาะสม\n\n"
            "⚝ ไม่ทักข้อความหานัสโดยตรงหรือแอดเฟรนนัสมาส่วนตัว แต่สามารถแท็กนัสเพื่อพูดคุยกันในช่องแชทดิสคอร์ดได้\n\n"
            "⚝ ไม่พาดพิงหรือเสียดสีเพื่อให้ผู้อื่นเสียหาย\n\n"
            "⚝ ห้ามส่งรูปภาพและข้อความลามกหรือคุกคามผู้อื่น\n\n"
            "⚝ ห้ามสแปมแชทหรือส่งข้อความซ้ำๆ รัวๆ สร้างความรำคาญให้แก่ผู้อื่น\n\n"
            "⚝ สามารถฝากคลิป / ฝากช่องของตัวเองได้ที่ห้อง <#1279197214069231656> และพิมพ์พูดคุยให้ถูกห้อง\n\n"
            "⚝ ซัพรายเดือนสามารถแท็กชวนนัสเล่นเกมได้เสมอในช่อง <#1267799728846802985> ถ้านัสไม่ติดอะไรเล่นด้วยแน่นอน\n\n"
            "⚝ ไม่อนุญาติให้โปรโมทช่องอื่น เว้นแต่ว่านัสอนุญาติแล้ว\n\n"
            "✿ หากทำผิดกฎ 2 ครั้ง จะมีการทักไปตักเตือนส่วนตัว หากมีครั้งที่ 3 จะถูกแบนออกดิสถาวรค่ะ  @everyone ✿"
        )

        message_sent = await message.channel.send(rules)
        await message_sent.add_reaction("✅")

# Get Twitch OAuth Token
def get_twitch_token():
    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(OAUTH_URL, params=params)
    return response.json().get('access_token')

# Get Twitch user ID by username
def get_user_id(twitch_username, token):
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    params = {'login': twitch_username}
    response = requests.get(USER_INFO_URL, headers=headers, params=params)
    data = response.json().get('data')
    if data:
        return data[0]['id'], data[0]['profile_image_url']
    return None, None

# Check if the user is live
def check_live_status(user_id, token):
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    params = {'user_id': user_id}
    response = requests.get(STREAMS_URL, headers=headers, params=params)
    streams = response.json().get('data')
    if streams:
        return streams[0]
    return None

# Task to check Twitch live status periodically
async def live_status_task():
    await client.wait_until_ready()
    channel = client.get_channel(1267797428849868811)  # ใส่ ID ของช่อง Discord ที่ต้องการให้บอทแจ้งเตือน
    token = get_twitch_token()
    user_id, icon_url = get_user_id(TWITCH_USERNAME, token)

    is_live = False

    while not client.is_closed():
        stream = check_live_status(user_id, token)
        if stream and not is_live:
            title = stream['title']
            game_name = stream['game_name']
            viewer_count = stream['viewer_count']
            thumbnail_url = stream['thumbnail_url'].replace("{width}x{height}", "1280x720")

            embed = discord.Embed(
                description=f'**[{title}](https://twitch.tv/{TWITCH_USERNAME})**',
                color=0x9146FF
            )
            embed.set_author(
                name=f'{TWITCH_USERNAME} is live on Twitch!',
                url=f'https://twitch.tv/{TWITCH_USERNAME}',
                icon_url=icon_url
            )
            embed.add_field(name='Game', value=game_name, inline=True)
            embed.add_field(name='Viewers', value=viewer_count, inline=True)
            embed.set_image(url=thumbnail_url)

            await channel.send(f'❥ Uranutsu กำลังสตรีมอยู่ เข้ามาพูดคุยกันได้นะคะ @everyone ʕ ᵒ ᴥ ᵒʔ', embed=embed)
            is_live = True
        elif not stream and is_live:
            await channel.send(f'{TWITCH_USERNAME} has ended their stream.')
            is_live = False

        await asyncio.sleep(60)  # รอ 60 วินาที

# เริ่มต้นการทำงานของบอท
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await tree.sync()
    client.loop.create_task(live_status_task())

server_on

client.run(DISCORD_TOKEN)
