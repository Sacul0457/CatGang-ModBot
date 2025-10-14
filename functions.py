from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Any
from uuid import uuid4
import base64
import asqlite
import re
from discord.utils import get
if TYPE_CHECKING:
    from main import ModBot
    from discord import Embed


#QUERIES
async def save_to_moddb(bot: ModBot, case_id: str, user_id: int, action: Literal['warn', 'ban', 'unmute', 'mute', 'kick', 'unban', 'unwarn', 'automodwarn', 'tempban'], 
                        mod_id: int, time: float, log_id: int) -> None:
    async with bot.mod_pool.acquire() as conn:
        await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)''',
                           (case_id, user_id, action, mod_id, time, log_id))
        await conn.commit()
async def save_to_appealdb(bot: ModBot, thread_id: int, user_id: int, action: str) -> None:
    async with bot.mod_pool.acquire() as conn:
        await conn.execute('''INSERT INTO appealdb (thread_id, user_id, action) VALUES (?, ?, ?)
                           ON CONFLICT(thread_id) DO UPDATE SET user_id = excluded.user_id, action = excluded.action''',
                           (thread_id, user_id, action))
        await conn.commit()
        
async def delete_from_appealdb(bot: ModBot, thread_id: int) -> None:
    async with bot.mod_pool.acquire() as conn:
        await conn.execute('''DELETE FROM appealdb WHERE thread_id = ?''',
                           (thread_id, ))
        await conn.commit()

async def double_query(bot: ModBot, *, query_one: str, value_one: tuple, query_two: str, value_two: tuple) -> None:
    async with bot.mod_pool.acquire() as conn:
        await conn.execute(query_one, value_one)
        await conn.execute(query_two, value_two)
        await conn.commit()

async def execute_sql(query: str) -> dict[str, Any]:
    async with asqlite.connect('mod.db') as conn:
        try:
            row = await conn.execute(query)
        except Exception as e:
            raise e
        result = await row.fetchall()
        return sql_to_dict(result)


#FUNCTIONS
def convert_to_base64() -> str:
    u = uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")

def sql_to_dict(sql_results: list[tuple]) -> dict[str, Any]:
    """Formats a sql.Row into dict"""

    possible_queries = ('case_id', 'user_id', 'time', 'action', 'mod_id', 'log_id', 'thread_id') #All the possible queries in all the tables
    data = {}
    for row in sql_results: # fetchall() returns a list of tuples, so we loop through the list
        for query in possible_queries: 
            try:
                value = row[query] # Try to fetch the value from the row
            except IndexError:
                continue
            if query in data: # For example 'SELECT user_id FROM epi_users', it will make user_id a list
                if not isinstance(data[query], list):
                    data[query] = [data[query]] if query in data else []
                data[query].append(value)
            else:
                data[query] = value

    return data
                
def get_field_content(embed: Embed, field_name: str) -> str | None:
        reported_by_field = get(embed.fields, name=field_name)
        if reported_by_field is None:
            return None
        return reported_by_field.value

def get_user_id_from_avatar(avatar_url: str) -> int | None:
    """Gets the user_id from a users avatar"""
    
    guild_member_avatar_regex = r"^https?:\/\/cdn\.discord(?:app)?\.com\/guilds\/\d+\/users\/\d+\/avatars\/"
    user_avatar_regex = r"^https?:\/\/cdn\.discord(?:app)?\.com\/avatars\/\d+\/"
    if re.match(user_avatar_regex, avatar_url, re.IGNORECASE):
        user_id = int(avatar_url.split("/")[4]) #https://cdn.discordapp.com/avatars/user_id/user_avatar.png -> ['https:', '', 'cdn.discordapp.com', 'avatars', 'user_id', 'user_avatar.png']
    elif re.match(guild_member_avatar_regex, avatar_url, re.IGNORECASE):
        user_id = int(avatar_url.split("/")[6]) #https://cdn.discordapp.com/guilds/guild_id/users/user_id/avatars/member_avatar.png -> ['https:', '', 'cdn.discordapp.com', 'guilds', 'guild_id', 'users', 'user_id', 'avatars', 'member_avatar.png']
    else:
        user_id = None
    return user_id