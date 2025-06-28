import discord
from discord.ext import commands
from discord import app_commands
import asqlite
import os
from dotenv import  load_dotenv
load_dotenv()
import asyncio
import datetime
import time
import random



TOKEN = os.getenv("TOKEN")

cogs = ("automod", "mod", "utilities")

async def main():
    async with asqlite.connect("mod.db") as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS moddb(
                           case_id TEXT  PRIMARY KEY,
                           user_id INTEGER,
                           action TEXT,
                           mod_id INTEGER) ''')
        await conn.execute('''CREATE INDEX IF NOT EXISTS user_id_index on moddb(user_id)''')
        await conn.execute('''CREATE INDEX IF NOT EXISTS mod_id_index on moddb(mod_id)''')

        await conn.execute('''CREATE TABLE IF NOT EXISTS tempbandb(
                           user_id INTEGER PRIMARY KEY,
                           time FLOAT) ''')
        await conn.execute('''CREATE INDEX IF NOT EXISTS time_index on tempbandb(time)''')
        await conn.commit()

asyncio.run(main())
class ModBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.none()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.guild_messages = True
        intents.moderation = True
        intents.auto_moderation = True
        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=intents, help_command=None)
    async def setup_hook(self):
        asyncio.get_event_loop().set_debug(True)
        self.mod_pool = await asqlite.create_pool("mod.db", size=4)
        await self.load_extension("mod")
    
    async def close(self):
        await self.mod_pool.close()
        await super().close()
bot = ModBot()

bot.run(TOKEN)
