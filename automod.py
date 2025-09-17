from __future__ import annotations

import discord
from discord.ext import commands
import time
import datetime
import asyncio
from uuid import uuid4
import base64
import re
from typing import TYPE_CHECKING
from functions import save_to_moddb, double_query, convert_to_base64
if TYPE_CHECKING:
    from main import ModBot


MOD_LOG = 1411982484744175638
NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
MODERATOR = 1319214233803816960
SENIOR = 1343556008223707156
ADMIN = (1319213465390284860, 1343556153657004074, 1356640586123448501, 1343579448020308008)
SACUL = 1294291057437048843
GUILD_ID = 1319213192064536607

MEDIA_CATEGORY= 1340256351317790730
REGEX_PATTERN = re.compile(r'https?:\/\/[^\s/$.?#].[^\s]*')

class AutomodCog(commands.Cog):
    def __init__(self, bot: ModBot):
        self.bot = bot
        self.last_executed = 0

    def convert_to_base64(self) -> str:
        u = uuid4()
        return base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")

    def calc_last_executed(self) -> bool:
        if time.time() - self.last_executed <= 7:
            return False
        self.last_executed = time.time()
        return True

    @commands.Cog.listener("on_message")
    async def message_listener(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild.id !=GUILD_ID:
            return
        bucket = self.bot.spam_limit.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after and self.calc_last_executed():
            await self.purge_messages(message.author, message.channel)

    async def purge_messages(
        self, member: discord.Member | discord.User , channel: discord.TextChannel
    ):
        await asyncio.sleep(2.5)

        def check(msg: discord.Message):
            return msg.author == member and msg.channel == channel

        await channel.purge(limit=15, check=check)
        await channel.send(
            f"{member.mention} let's avoid spamming!\
                                    \n-# ⚠️ Repeating this can lead into a warning, please read <#1319606464264011806>.",
            delete_after=5.0,
        )
        await self.warn_user(member, channel)

    async def warn_user(
        self, user: discord.Member | discord.User, channel: discord.TextChannel
    ) -> None:
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute(
                """SELECT NULL from moddb WHERE user_id =? AND action = ? """,
                (user.id, "automodwarn"),
            )
            results = await rows.fetchall()
        warns = len(results) + 1 or 0
        action = None
        if warns == 10:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(
                    title="You have been autobanned (10 warns)",
                    description=f">>> **Duration:** Permanent\
                                        \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                    timestamp=discord.utils.utcnow(),
                    color=discord.Color.brand_red(),
                )

                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed, view=AppealView())
                except discord.Forbidden:
                    pass
            try:
                await user.guild.ban(
                    user, reason=f"AutoBanned for: Spam: `>= 5 messages in 3.5s`"
                )
            except discord.Forbidden as e:
                return print(e)
            except Exception as e:
                print(f"An error occurred: {e}")
            log_channel = self.bot.get_channel(MOD_LOG)
            case_id = convert_to_base64()

            embed = discord.Embed(
                title=f"Autobanned (`{case_id}`) | 10 warns",
                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Duration:** Permanent\
                                    \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_red(),
            )

            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            log_message = await log_channel.send(embed=embed)

            action = "ban"
        elif warns == 8:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(
                    title="You have been automuted (8 warns)",
                    description=f">>> **Duration:** 1 day\
                                        \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                    timestamp=discord.utils.utcnow(),
                    color=discord.Color.brand_red(),
                )

                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed, view=AppealView())
                except discord.Forbidden:
                    pass
            try:
                await user.timeout(
                    datetime.timedelta(days=1),
                    reason=f"Automuted for: Spam: `>= 5 messages in 3.5s`",
                )
            except discord.Forbidden as e:
                return print(e)
            except Exception as e:
                return print(f"An error occurred: {e}")
            log_channel = self.bot.get_channel(MOD_LOG)
            case_id = convert_to_base64()

            embed = discord.Embed(
                title=f"Automuted (`{case_id}`) | 8 warns",
                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Duration:** 1 day\
                                    \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_red(),
            )

            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            log_message = await log_channel.send(embed=embed)
            action = "mute"
        elif warns == 5:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(
                    title="You have been automuted (5 warns)",
                    description=f">>> **Duration:** 6 hours\
                                        \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                    timestamp=discord.utils.utcnow(),
                    color=discord.Color.brand_red(),
                )

                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed, view=AppealView())
                except discord.Forbidden:
                    pass
            try:
                await user.timeout(
                    datetime.timedelta(hours=6),
                    reason=f"Automuted for: Spam: `>= 5 messages in 3.5s`",
                )
            except discord.Forbidden as e:
                return print(e)
            except Exception as e:
                print(f"An error occurred: {e}")
            log_channel = self.bot.get_channel(MOD_LOG)
            case_id = convert_to_base64()
            embed = discord.Embed(
                title=f"Automuted (`{case_id}`) | 5 warns",
                description=f">>> **User:** {user.mention} ({user.id})\
                        \n**Channel**: {channel.mention}\
                        \n**Duration:** 6 hours\
                        \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_red(),
            )

            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            log_message = await log_channel.send(embed=embed)
            action = "mute"
        elif warns == 2:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(
                    title="You have been autowarned (2 warns)",
                    description=f">>> **Reason:** Spam: `>= 5 messages in 3.5s`",
                    timestamp=discord.utils.utcnow(),
                    color=discord.Color.brand_red(),
                )

                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed, view=AppealView())
                except discord.Forbidden:
                    pass
            log_channel = self.bot.get_channel(MOD_LOG)
            case_id = convert_to_base64()

            embed = discord.Embed(
                title=f"Autowarned (`{case_id}`) | 2 warns",
                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_red(),
            )

            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            log_message = await log_channel.send(embed=embed)
            action = "warn"
        else:
            log_channel = self.bot.get_channel(MOD_LOG)

            embed = discord.Embed(
                title=f"Automod Spam",
                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Reason:** Spam: `>= 5 messages in 3.5s`",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_red(),
            )

            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            log_message = await log_channel.send(embed=embed)

        automod_case_id = convert_to_base64()
        if action:
            await double_query(self.bot, query_one='''INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)''', 
                               value_one=(automod_case_id, user.id, "automodwarn", self.bot.user.id, time.time(), log_message.id),
                               query_two='''INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)''',
                               value_two=(case_id, user.id, action, self.bot.user.id, time.time(), log_message.id)
                               )
        else:
            await save_to_moddb(self.bot, automod_case_id, user.id, 'automodwarn', self.bot.user.id, time.time(), log_message.id)


    @commands.Cog.listener('on_message')
    async def media_listener(self, message: discord.Message):
        if isinstance(message.channel,  discord.TextChannel) and message.channel.category_id and message.channel.category_id == MEDIA_CATEGORY and not message.author.bot:
            has_link : str | None = REGEX_PATTERN.search(message.content)
            if not message.attachments and has_link is None:
                try:
                    await message.delete()
                except discord.NotFound:
                    return

async def setup(bot: commands.Bot):
    await bot.add_cog(AutomodCog(bot))


class AppealView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Appeal",
                style=discord.ButtonStyle.link,
                url="https://discord.gg/er2ErWNZjG",
            )
        )
