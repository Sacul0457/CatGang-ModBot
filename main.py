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


TOKEN = os.getenv("TEST_TOKEN")

cogs = ("mod", "logs", "automod")

async def main():
    async with asqlite.connect("mod.db") as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS moddb(
                           case_id TEXT PRIMARY KEY, 
                           user_id INTEGER,
                           action TEXT,
                           mod_id INTEGER,
                           time FLOAT) ''')
        await conn.execute('''CREATE INDEX IF NOT EXISTS user_id_index on moddb(user_id)''')
        await conn.execute('''CREATE INDEX IF NOT EXISTS mod_id_index on moddb(mod_id)''')
        await conn.execute('''CREATE INDEX IF NOT EXISTS time_index on moddb(time)''')

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
        #intents.moderation = True
        intents.auto_moderation = True
        intents.emojis_and_stickers = True
        super().__init__(command_prefix=commands.when_mentioned_or("-"), intents=intents, help_command=None)
        self.spam_limit = commands.CooldownMapping.from_cooldown(5, 2.5, type=commands.BucketType.member)
    async def setup_hook(self):
        self.mod_pool = await asqlite.create_pool("mod.db", size=4)
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"Loaded: {cog}")
            except Exception as e:
                print(f"An error occurred: {e}")
        asyncio.get_event_loop().set_debug(True)

    
    
    async def close(self):
        await self.mod_pool.close()
        await super().close()
bot = ModBot()

@bot.event
async def on_command_error(ctx:commands.context, error:commands.CommandError):
    pass

@bot.group(name="cog")
async def cog(ctx:commands.Context, cog:str) -> None:
    if ctx.author.id != 802167689011134474:
        return
    if ctx.invoked_subcommand is None:
        await ctx.send(f"You need to load, reload or unload.")
@cog.command()
async def load(ctx:commands.Context, cog:str) -> None:
    if ctx.author.id != 802167689011134474:
        return
    await ctx.message.delete()
    if cog not in cogs:
        await ctx.send(f"You must choose from: {cogs}",
                       delete_after=5.0)
    await bot.load_extension(cog)

@cog.command()
async def reload(ctx:commands.Context, cog:str) -> None:
    if ctx.author.id != 802167689011134474:
        return
    await ctx.message.delete()
    if cog not in cogs:
        await ctx.send(f"You must choose from: {cogs}",
                       delete_after=5.0)
    await bot.reload_extension(cog)

@cog.command()
async def unload(ctx:commands.Context, cog:str) -> None:
    if ctx.author.id != 802167689011134474:
        return
    await ctx.message.delete()
    if cog not in cogs:
        await ctx.send(f"You must choose from: {cogs}",
                       delete_after=5.0)
    await bot.unload_extension(cog)


bot.run(TOKEN)
