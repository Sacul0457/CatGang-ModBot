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



@bot.command()
async def fetch(ctx:commands.Context, member_or_case : discord.User | str):
    if isinstance(member_or_case, discord.User):
        async with bot.mod_pool.acquire() as conn:
            row = await conn.execute('''SELECT case_id, action, mod_id FROM moddb WHERE user_id =?''',
                               (member_or_case.id,))
            result = await row.fetchall()
        if result is None:
            return await ctx.send(f"{member_or_case} has no cases!")
        elif isinstance(result, list):
            data_list = "\n- ".join([f"Case: `{item['case_id']}`, Action: {item['action']}, Mod: `{item['mod_id']}`" for item in result])
            await ctx.send(f"- {data_list}")

        else:
            case_id = result["case_id"]
            action = result["action"]
            mod_id = result["mod_id"]
            await ctx.send(f"Case: `{case_id}`\nAction: {action}\nMod ID: `{mod_id}`")
    elif isinstance(member_or_case, str):
        async with bot.mod_pool.acquire() as conn:
            row = await conn.execute('''SELECT user_id, action, mod_id FROM moddb WHERE case_id =?''',
                               (member_or_case,))
            result = await row.fetchone()
        if result:
            user_id = result["user_id"]
            action = result["action"]
            mod_id = result["mod_id"]
            await ctx.send(f"User_id: `{user_id}`\nAction: {action}\nMod ID: `{mod_id}`")
        else:
            await ctx.send(f"No such case: `{member_or_case}`!")


bot.run(TOKEN)
