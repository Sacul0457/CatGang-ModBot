from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Any
from uuid import uuid4
import base64
if TYPE_CHECKING:
    from main import ModBot


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
                           ON CONFLICT DO UPDATE SET user_id = user_id''',
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


#FUNCTIONS
def convert_to_base64() -> str:
    u = uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")
