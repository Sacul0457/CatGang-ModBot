import discord
from discord.ext import commands
import time
import datetime
import asyncio
from uuid import uuid4
import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import ModBot

MOD_LOG =1350425247471636530
MOD_LOG =  1350425247471636530
NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
MODERATOR = 1319214233803816960
SENIOR = 1343556008223707156
ADMIN = (1319213465390284860, 1343556153657004074, 1356640586123448501, 1343579448020308008)
SACUL = 1294291057437048843
GUILD_ID = 1319213192064536607

class AutomodCog(commands.Cog):
    def __init__(self, bot : ModBot):
        self.bot = bot
        self.last_executed = 0
    def convert_to_base64(self) ->str:
        u = uuid4()
        return base64.urlsafe_b64encode(u.bytes).rstrip(b'=').decode('ascii')
 
    def calc_last_executed(self) ->bool:
        if time.time() - self.last_executed <= 7:
            return False
        self.last_executed = time.time()
        return True
    @commands.Cog.listener("on_message")
    async def message_listener(self, message:discord.Message):
        if message.author.bot:
            return
        bucket = self.bot.spam_limit.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after and self.calc_last_executed():
            await self.purge_messages(message.author, message.channel)
            

    async def purge_messages(self, member:discord.Member, channel:discord.TextChannel):
        await asyncio.sleep(2.5)
        def check(msg:discord.Message):
            return msg.author == member and msg.channel == channel
        await channel.purge(limit=15, check=check)
        await channel.send(f"{member.mention} let's avoid spamming!\
                                    \n-# ⚠️ Repeating this can lead into a warning, please read <#1319606464264011806>.", delete_after=5.0)
        await self.warn_user(member, channel)

        
    async def warn_user(self, user: discord.Member | discord.User, channel:discord.TextChannel) -> None:
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute('''SELECT NULL from moddb WHERE user_id =? AND action = ? ''',
                                         (user.id, "automodwarn"))
            results = await rows.fetchall()
        warns = len(results) + 1 or 0
        action = None
        if warns == 10:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(title="You have been autobanned (10 warns)",
                                    description=f">>> **Duration:** Permanent\
                                        \n**Reason:** Spam: `>= 5 messages in 3s`",
                                        timestamp=discord.utils.utcnow(),
                                        color=discord.Color.brand_red())
                
                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed, view=AppealView())
                except discord.Forbidden:
                    pass
            try:
                await user.guild.ban(user, reason=f"AutoBanned for: Spam: `>= 5 messages in 3s`")
            except discord.Forbidden as e:
                return print(e)
            except Exception as e:
                await print(f"An error occurred: {e}")
            channel = user.guild.get_channel(MOD_LOG)
            case_id = self.convert_to_base64()
            
            embed = discord.Embed(title=f"Autobanned (`{case_id}`) | 10 warns",
                                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Duration:** Permanent\
                                    \n**Reason:** Spam: `>= 5 messages in 3s`",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)

            action = "ban"
        elif warns == 8:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(title="You have been automuted (8 warns)",
                                    description=f">>> **Duration:** 1 day\
                                        \n**Reason:** Spam: `>= 5 messages in 3s`",
                                        timestamp=discord.utils.utcnow(),
                                        color=discord.Color.brand_red())
                
                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed)
                except discord.Forbidden:
                    pass
            try:
                await user.timeout(datetime.timedelta(days=1), reason=f"Automuted for: Spam: `>= 5 messages in 3s`")
            except discord.Forbidden as e:
                return print(e)
            except Exception as e:
                return print(f"An error occurred: {e}")
            channel = user.guild.get_channel(MOD_LOG)
            case_id = self.convert_to_base64()
            
            embed = discord.Embed(title=f"Automuted (`{case_id}`) | 8 warns",
                                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Duration:** 1 day\
                                    \n**Reason:** Spam: `>= 5 messages in 3s`",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)
            action = "mute"
        elif warns == 5:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(title="You have been automuted (5 warns)",
                                    description=f">>> **Duration:** 6 hours\
                                        \n**Reason:** Spam: `>= 5 messages in 3s`",
                                        timestamp=discord.utils.utcnow(),
                                        color=discord.Color.brand_red())
                
                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed)
                except discord.Forbidden:
                    pass
            try:
                await user.timeout(datetime.timedelta(hours=6), reason=f"Automuted for: Spam: `>= 5 messages in 3s`")
            except discord.Forbidden as e:
                return print(e)
            except Exception as e:
                await print(f"An error occurred: {e}")
            channel = user.guild.get_channel(MOD_LOG)
            case_id = self.convert_to_base64()
            embed = discord.Embed(title=f"Automuted (`{case_id}`) | 5 warns",
                    description=f">>> **User:** {user.mention} ({user.id})\
                        \n**Channel**: {channel.mention}\
                        \n**Duration:** 6 hours\
                        \n**Reason:** Spam: `>= 5 messages in 3s`",
                        timestamp=discord.utils.utcnow(),
                        color=discord.Color.brand_red())
            
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)
            action = "mute"
        elif warns == 2:
            if isinstance(user, discord.Member) and not user.bot:
                user_embed = discord.Embed(title="You have been autowarned (2 warns)",
                                    description=f">>> **Reason:** Spam: `>= 5 messages in 3s`",
                                        timestamp=discord.utils.utcnow(),
                                        color=discord.Color.brand_red())
                
                user_embed.set_author(name=user.guild, icon_url=user.guild.icon.url)
                user_embed.set_thumbnail(url=user.guild.icon.url)
                try:
                    await user.send(embed=user_embed)
                except discord.Forbidden:
                    pass
            channel = user.guild.get_channel(MOD_LOG)
            case_id = self.convert_to_base64()
            
            embed = discord.Embed(title=f"Autowarned (`{case_id}`) | 2 warns",
                                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Reason:** Spam: `>= 5 messages in 3s`",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)
            action = "warn"
        else:
            channel = user.guild.get_channel(MOD_LOG)
            
            embed = discord.Embed(title=f"Automod Spam",
                                description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Channel**: {channel.mention}\
                                    \n**Reason:** Spam: `>= 5 messages in 3s`",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)

        automod_case_id = self.convert_to_base64()
        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                                (automod_case_id, user.id, "automodwarn", self.bot.user.id, time.time()))
            if action:
                await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                                   (case_id, user.id, action, self.bot.user.id, time.time()))


async def setup(bot:commands.Bot):
    await bot.add_cog(AutomodCog(bot))

class AppealView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Appeal", style=discord.ButtonStyle.link, url="https://discord.gg/er2ErWNZjG"))
