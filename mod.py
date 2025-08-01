from __future__ import annotations

import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import time
import os
import random
import string
from uuid import uuid4
import base64
import paginator
ButtonPaginator = paginator.ButtonPaginator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import ModBot

MOD_LOG =  1350425247471636530
NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
MODERATOR = 1319214233803816960
SENIOR = 1343556008223707156
ADMIN = (1319213465390284860, 1343556153657004074, 1356640586123448501, 1343579448020308008)
SACUL = 1294291057437048843
GUILD_ID = 1319213192064536607
def convert_to_base64():
    u = uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b'=').decode('ascii')

class ModCog(commands.Cog):
    def __init__(self, bot:ModBot):
        self.bot = bot
    
    async def cog_load(self):
        self.auto_unban.start()


    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, MODERATOR, SACUL)
    async def resetnickname(self, ctx:commands.Context, member: discord.Member):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            embed = discord.Embed(title="Insufficient Permissions",
                                  description=f"- You cannot reset a member's nickname who's role is higher than or equal to yours.",
                                  color=discord.Color.brand_red())
            return await ctx.send(embed=embed, delete_after=5.0)      
        if member.nick is None:
            embed = discord.Embed(title="No Nickname Set",
                                  description=f"- {member.mention} does not have a nickname.",
                                  color=discord.Color.brand_red())
            return await ctx.send(embed=embed, delete_after=5.0)
        nickname = member.nick
        try:
            await member.edit(nick=None)
        except discord.Forbidden as e:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {e}",
                                  color=discord.Color.brand_red())
            return await ctx.send(embed=embed, delete_after=5.0)
        
        channel_embed = discord.Embed(title=f"✅ Successfully reset `@{member}`'s nickname",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)
        channel = ctx.guild.get_channel(MOD_LOG)
        embed = discord.Embed(title="Nickname Reset",
                              description=f">>> **User:** {member.mention} ({member.id})\n**Before reset:** `{nickname}`",
                              color=discord.Color.brand_red(),
                              timestamp=discord.utils.utcnow())
        embed.add_field(name=f"Resetted by",
                        value=f"{ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        await channel.send(embed=embed)

    @resetnickname.error
    async def resetnickname_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!warn [user]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, MODERATOR, SACUL, SENIOR)
    async def warn(self, ctx:commands.Context, member:discord.Member,  *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            embed = discord.Embed(title="Insufficient Permissions",
                                  description=f"- You cannot warn a member who's role is higher than or equal to yours.",
                                  color=discord.Color.brand_red())
            return await ctx.send(embed=embed)
        
        case_id = convert_to_base64()
        user_embed = discord.Embed(title="You have been warned",
                            description=f">>> **Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
        
        user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        user_embed.set_thumbnail(url=ctx.guild.icon.url)
        if not member.bot:
            try:
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass
        channel_embed = discord.Embed(title=f"✅ Successfully warned `@{member}`",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)
        channel = ctx.guild.get_channel(MOD_LOG)
        embed = discord.Embed(title=f"Warned (`{case_id}`)",
                            description=f">>> **User:** {member.mention} ({member.id})\
                                \n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
        
        embed.add_field(name=f"Warned by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                               (case_id, member.id, "warn", ctx.author.id, time.time()))
            await conn.commit()
    @warn.error
    async def warn_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!warn [user] [reason]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, MODERATOR, SACUL, SENIOR)
    async def deletewarns(self, ctx:commands.Context, member:discord.Member,  *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            embed = discord.Embed(title="Insufficient Permissions",
                                  description=f"- You cannot remove a member's warns who's role is higher than or equal to yours.",
                                  color=discord.Color.brand_red())
            #return await ctx.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute('''SELECT case_id FROM moddb WHERE user_id = ? AND action = ?''',
                               (member.id, "warn"))
            results = await rows.fetchall()
            if not results:
                embed = discord.Embed(title="No Warns Found",
                                      description=f"{member.mention} has no warns.",
                                      color=discord.Color.brand_red())
                return await ctx.send(embed=embed)
            case_ids =[result["case_id"] for result in results]
            case_id = convert_to_base64()
            await conn.execute(f'''DELETE FROM moddb WHERE case_id IN ({",".join("?" for _ in case_ids)})''',
                               tuple(case_ids))
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                               (case_id, member.id, "unwarn", ctx.author.id, time.time()))

            await conn.commit()

        user_embed = discord.Embed(title="You have been unwarned",
                            description=f">>> **Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())
        
        user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        user_embed.set_thumbnail(url=ctx.guild.icon.url)
        if not member.bot:
            try:
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass
        channel_embed = discord.Embed(title=f"✅ Successfully unwarned `@{member}`",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)
        channel = ctx.guild.get_channel(MOD_LOG)
        embed = discord.Embed(title=f"Unwarned (`{case_id}`)",
                            description=f">>> **User:** {member.mention} ({member.id})\
                                \n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())
        
        embed.add_field(name=f"Unwarned by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @deletewarns.error
    async def unwarn_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!deletewarns [user] [reason]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
            
    @tasks.loop(seconds=30)
    async def auto_unban(self):
        async with self.bot.mod_pool.acquire() as conn:
            row= await conn.execute('''SELECT user_id, time, log_id FROM tempbandb
                               ORDER BY time ASC
                               LIMIT 1''')
            result = await row.fetchone()
            if result:
                user_id = result["user_id"]
                row2 = await conn.execute('''SELECT case_id, mod_id, time FROM moddb WHERE user_id = ? AND action = ?''',
                                        (user_id, "tempban"))
                case_data = await row2.fetchone()
        if not result:
            self.auto_unban.cancel()
            return
        to_sleep_timestamp = result["time"]
        to_sleep = datetime.datetime.fromtimestamp(to_sleep_timestamp)
        await discord.utils.sleep_until(to_sleep)

        try:
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
        except discord.NotFound:
            async with self.bot.mod_pool.acquire() as conn:
                await conn.execute('''DELETE FROM tempbandb WHERE user_id =?''',
                                   (int(user_id,)))
                await conn.commit()
            return
        
        try:
            mod = self.bot.get_user(case_data["mod_id"]) or await self.bot.fetch_user(case_data["mod_id"])
        except discord.NotFound:
            async with self.bot.mod_pool.acquire() as conn:
                await conn.execute('''DELETE FROM tempbandb WHERE user_id =?''',
                                   (int(user_id,)))
                await conn.commit()
            return
        
        guild = self.bot.get_guild(GUILD_ID)
        try:
            await guild.unban(user, reason=f"Tempban Expired")
        except discord.Forbidden:
            return
        banned_on = case_data["time"]
        channel = self.bot.get_channel(MOD_LOG)
        log_id = result["log_id"]
        case_id = convert_to_base64()
        embed = discord.Embed(title=f"Unbanned | Tempban Expired (`{case_id}`)",
                              description=f">>> **User:** {user.mention} ({user.id})\n**Case Id:** `{case_id}`\
                                \n**Mod:** {mod.mention} ({mod.id})\n**Banned on:** <t:{int(banned_on)}:f>",
                                color=discord.Color.brand_green(),
                                timestamp=discord.utils.utcnow())
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{mod}", icon_url=mod.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        await channel.send(embed=embed, view=PreviousCase(log_id))
        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''DELETE FROM tempbandb WHERE user_id = ?''',
                               (user_id,))
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                               (case_id, user_id, "unban", mod.id, time.time()))
            await conn.commit()
        
    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    async def ban(self, ctx:commands.Context, member : discord.Member | discord.User, duration : str = "Permanent", *, reason:str = "No reason provided.") -> None:
        await ctx.message.delete()
        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(title="Insufficient Permissions",
                                    description=f"- You cannot ban a member who's role is higher than or equal to yours.",
                                    color=discord.Color.brand_red())
                return await ctx.send(embed=embed)
            
        elif isinstance(member, discord.User):
            async for entry in ctx.guild.bans():
                if entry.user.id == member.id:
                        embed = discord.Embed(title="Already Banned",
                                        description=f"- {member.mention} is already banned.",
                                        color=discord.Color.brand_red())
                        return await ctx.send(embed=embed)
                    
        total_seconds = None
        if duration != "Permanent":
            if duration.endswith(("s", "m", "h", "d")) and any(num in duration for num in NUMBERS):
                td = datetime.timedelta()
                duration_list = [duration for duration in duration.split(",")]
                for duration in duration_list:
                    if duration.endswith("s"):
                        new_time = duration.strip("s")
                        td += datetime.timedelta(seconds=int(new_time))
                    elif duration.endswith("m"):
                        new_time = duration.strip("m")
                        td +=  datetime.timedelta(minutes= int(new_time))
                    elif duration.endswith("h"):
                        new_time = duration.strip("h")
                        td +=  datetime.timedelta(hours= int(new_time))
                    elif duration.endswith("hour"):
                        new_time = duration.strip("hour")
                        td +=  datetime.timedelta(hours= int(new_time))
                    elif duration.endswith("d"):
                        new_time = duration.strip("d")
                        td +=  datetime.timedelta(days= int(new_time))

                total_seconds = int(td.total_seconds() + time.time())
        final_reason = reason if duration != "Permanent" else f"{duration} {reason}" if reason != "No reason provided." else duration if duration != "Permanent" else "No reason provided."
        final_duration = f"**Duration:** Permanent" if not total_seconds  else f"**Unbanned:** <t:{total_seconds}:R>"
        if isinstance(member, discord.Member) and not member.bot:
            user_embed = discord.Embed(title="You have been banned",
                                description=f">>> {final_duration}\
                                    \n**Reason:** {final_reason}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            
            user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            user_embed.set_thumbnail(url=ctx.guild.icon.url)
            try:
                await member.send(embed=user_embed, view=AppealView())
            except discord.Forbidden:
                pass
        try:
            await ctx.guild.ban(member, reason=f"Banned by {ctx.author} for: {final_reason}")
        except discord.Forbidden as e:
            return await ctx.send(f"An error occurred: {e}", 
                                delete_after=5.0)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

        channel_embed = discord.Embed(title=f"✅ Successfully banned `@{member}`",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)

        channel = ctx.guild.get_channel(MOD_LOG)
        case_id = convert_to_base64()

        embed = discord.Embed(title=f"Banned (`{case_id}`)",
                            description=f">>> **User:** {member.mention} ({member.id})\
                                \n{final_duration}\
                                \n**Reason:** {final_reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
        
        embed.add_field(name=f"Banned by", value=f" >>> {ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        log_message = await channel.send(embed=embed)

        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?) ''',
                               (case_id, member.id, f"{"ban" if not total_seconds else "tempban"}", ctx.author.id,  time.time()))

            if total_seconds:
                await conn.execute('''INSERT INTO tempbandb (user_id, time, log_id) VALUES (?, ?, ?)
                                    ON CONFLICT(user_id) DO UPDATE SET time=excluded.time, log_id=excluded.log_id''',
                                    (member.id, (td.total_seconds() + time.time()), log_message.id))
            await conn.commit()
        if total_seconds:
            self.auto_unban.start() if not self.auto_unban.is_running() else self.auto_unban.restart()

    @ban.error
    async def ban_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!ban [user] [duration] [reason]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return  
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    async def unban(self, ctx:commands.Context, user:discord.User, *, reason:str="No reason provided."):
        await ctx.message.delete()
        bans = [entry.user.id async for entry in ctx.guild.bans()]
        if user.id not in bans:
            embed = discord.Embed(title="User Not Banned",
                                description=f"- {user.mention} is not banned.",
                                    color=discord.Color.brand_red())
            return await ctx.send(embed=embed)
        try:
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author} for: {reason}")
        except discord.Forbidden as e:
            embed = discord.Embed(title="An Error Occurred ",
                                  description=f"- {e}",
                                    color=discord.Color.brand_red())
            return await ctx.send(embed=embed)

        channel_embed = discord.Embed(title=f"✅ Successfully unbanned `@{user}`",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)
        case_id = convert_to_base64()
        channel = ctx.guild.get_channel(MOD_LOG)
        embed = discord.Embed(title=f"Unbanned (`{case_id}`)",
                            description=f">>> **User:** {user.mention} ({user.id})\
                                \n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())

        embed.add_field(name=f"Unbanned by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        await channel.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            tempban_row = await conn.execute('''SELECT NULL FROM tempbandb WHERE user_id = ?''',
                                             (user.id,))
            tempban_result = await tempban_row.fetchone()
            if tempban_result:
                await conn.execute('''DELETE FROM tempbandb WHERE user_id = ?''',
                                   (user.id,))
                
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                               (case_id, user.id, "unban", ctx.author.id, time.time()))
            await conn.commit()
    @unban.error
    async def unban_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!unban [user] [reason]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.UserNotFound):
            embed = discord.Embed(title="User Not Found",
                                  description=f"- `{error.argument}` is not a user.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SACUL, SENIOR)
    async def kick(self, ctx:commands.Context, member:discord.Member,  *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            embed = discord.Embed(title="Insufficient Permissions",
                                description=f"- You cannot kick a member who's role is higher than or equal to yours.",
                                color=discord.Color.brand_red())
            return await ctx.send(embed=embed)
        case_id = convert_to_base64()

        user_embed = discord.Embed(title="You have been kicked",
                            description=f">>> **Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
        
        user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        user_embed.set_thumbnail(url=ctx.guild.icon.url)
        if not member.bot:
            try:
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass
        try:
            await ctx.guild.kick(member, reason=f"Kicked by {ctx.author} for {reason}")
        except discord.Forbidden as e:
            embed = discord.Embed(title="An Error Occurred",
                                description=f"- {e}",
                                    color=discord.Color.brand_red())
            return await ctx.send(embed=embed)
        
        channel_embed = discord.Embed(title=f"✅ Successfully kicked `@{member}`",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)

        channel = ctx.guild.get_channel(MOD_LOG) or await ctx.guild.fetch_channel(MOD_LOG)
        embed = discord.Embed(title=f"Kicked (`{case_id}`)",
                            description=f">>> **User:** {member.mention} ({member.id})\
                                \n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
        
        embed.add_field(name=f"Kicked by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                            (case_id, member.id, "kick", ctx.author.id, time.time()))
            await conn.commit()
    @kick.error
    async def kick_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!kick [user] [reason]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, MODERATOR, SACUL)
    async def mute(self, ctx:commands.Context, member:discord.Member, duration:str, *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(title="Insufficient Permissions",
                                    description=f"- You cannot mute a member who's role is higher than or equal to yours.",
                                    color=discord.Color.brand_red())
                return await ctx.send(embed=embed)
        elif member.guild_permissions.administrator:
                embed = discord.Embed(title="Insufficient Permissions",
                                    description=f"- You mute an admin.",
                                    color=discord.Color.brand_red())
                return await ctx.send(embed=embed)
        td = datetime.timedelta()
        duration_list = [duration for duration in duration.split(",")]
        for duration in duration_list:
            if duration.endswith("s"):
                new_time = duration.strip("s")
                td += datetime.timedelta(seconds=int(new_time))
            elif duration.endswith("m"):
                new_time = duration.strip("m")
                td +=  datetime.timedelta(minutes= int(new_time))
            elif duration.endswith("h"):
                new_time = duration.strip("h")
                td +=  datetime.timedelta(hours= int(new_time))
            elif duration.endswith("hour"):
                new_time = duration.strip("hour")
                td +=  datetime.timedelta(hours= int(new_time))
            elif duration.endswith("d"):
                new_time = duration.strip("d")
                td +=  datetime.timedelta(days= int(new_time))
            else:
                embed = discord.Embed(title="Invalid Duration",
                                      description=f"- `{duration}` is not a valid duration.")
                return await ctx.send(embed=embed, delete_after=5.0)

        total_seconds = int(td.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if days > 28:
            embed = discord.Embed(title="Invalid Duration",
                                  description=f"- The maximum mute time is 28 days. Please set a mute time below it.")
            return await ctx.send(embd=embed, delete_after=5.0)
        try:
            await member.timeout(td, reason=f"Muted by {ctx.author} for: {reason}")
        except discord.Forbidden as e:
            embed = discord.Embed(title="An Error Occurred",
                                description=f"- {e}",
                                    color=discord.Color.brand_red())
            return await ctx.send(embed=embed)
        case_id = convert_to_base64()
        duration_message_parts = []
        if days > 0:
            duration_message_parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            duration_message_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            duration_message_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds > 0:
            duration_message_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        duration_message = ' and '.join(duration_message_parts)
        user_embed = discord.Embed(title="You have been muted",
                            description=f">>> **Duration:** {duration_message}\
                                \n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
        
        user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        user_embed.set_thumbnail(url=ctx.guild.icon.url)
        if not member.bot:
            try:
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass
        channel_embed = discord.Embed(title=f"✅ Successfully muted `@{member}`",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)

        channel = ctx.guild.get_channel(MOD_LOG)
        embed = discord.Embed(title=f"Muted (`{case_id}`)",
                            description=f">>> **User:** {member.mention} ({member.id})\
                                \n**Duration:** {duration_message}\n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
        embed.add_field(name=f"Muted by", value=f" >>> {ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                               (case_id, member.id, "mute", ctx.author.id, time.time()))
            await conn.commit()
    @mute.error
    async def mute_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!mute [user] [duration] [reason]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @commands.command()
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, MODERATOR, SACUL)
    async def unmute(self, ctx:commands.Context, member:discord.Member, *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(title="Insufficient Permissions",
                                    description=f"- You cannot unmute a member who's role is higher than or equal to yours.",
                                    color=discord.Color.brand_red())
                return await ctx.send(embed=embed)
        elif not member.is_timed_out():
                embed = discord.Embed(title="Member Not Muted",
                                    description=f"- {member.mention} is not muted.",
                                    color=discord.Color.brand_red())
                return await ctx.send(embed=embed)
        try:
            await member.timeout(None, reason=f"Unmuted by {ctx.author} for reason: {reason}")
        except discord.Forbidden as e:
            embed = discord.Embed(title="An error Occurred",
                                description=f"- {e}",
                                color=discord.Color.brand_red())
            return await ctx.send(embed=embed)


        user_embed = discord.Embed(title="You have been unmuted",
                            description=f">>> **Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())
        
        user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        user_embed.set_thumbnail(url=ctx.guild.icon.url)
        if not member.bot:
            try:
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass

        channel_embed = discord.Embed(title=f"✅ Successfully unmuted `@{member}`",
                                      color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=5.0)

        case_id = convert_to_base64()
        channel = ctx.guild.get_channel(MOD_LOG)
        embed = discord.Embed(title=f"Unmuted (`{case_id}`)",
                            description=f">>> **User:** {member.mention} ({member.id})\
                                \n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())

        embed.add_field(name=f"Unmuted by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                               (case_id, member.id, "unmute", ctx.author.id, time.time()))
            await conn.commit()
    @unmute.error
    async def unmute_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!unmute [user] [reason]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.group(name="clean", invoke_without_command=True)
    @commands.guild_only()
    async def clean(self, ctx:commands.Context, limit : int, channel : discord.TextChannel | None = None) -> None:
        await ctx.message.delete()
        if limit > 800:
            return await ctx.send(f"You can only purge up to `800` messages.", delete_after=5.0)
        def check(msg:discord.Message):
            return int(time.time() - msg.created_at.timestamp()) < datetime.timedelta(days=13).total_seconds()
        channel = channel or ctx.channel
        purged = await channel.purge(limit=limit, check=check)
        embed = discord.Embed(title=f"✅ Successfully purged `{len(purged)}` messages from {channel.mention}",
                              color=discord.Color.brand_green())
        await channel.send(embed=embed, delete_after=5)

    @clean.error
    async def clean_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!clean [limit] [channel]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.ChannelNotFound):
            embed = discord.Embed(title="Channel Not Found",
                                  description=f"- `{error.argument}` is not a channel.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @clean.command(name="until")
    @commands.guild_only()
    async def clean_until(self, ctx:commands.Context, until : str, channel :discord.TextChannel | None = None):
        def check(msg:discord.Message):
            return int(time.time() - msg.created_at.timestamp()) < datetime.timedelta(days=13).total_seconds()
        channel = channel or ctx.channel
        if "/" in until:
            until = until.split("/")[6]
        until = discord.utils.snowflake_time(int(until))
        purged = await channel.purge(after=until, check=check)
        embed = discord.Embed(title=f"✅ Successfully purged `{len(purged)}` messages from {channel.mention}",
                              color=discord.Color.brand_green())
        await channel.send(embed=embed, delete_after=5)

    @clean_until.error
    async def cleanuntil_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!clean until [msg] [channel]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.ChannelNotFound):
            embed = discord.Embed(title="Channel Not Found",
                                  description=f"- `{error.argument}` is not a channel.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @clean.command(name="between")
    @commands.guild_only()
    async def clean_between(self, ctx:commands.Context, first_message : str | int, second_message :str | int,  channel :discord.TextChannel | None = None):
        await ctx.message.delete()
        def check(msg:discord.Message):
            return int(time.time() - msg.created_at.timestamp()) < datetime.timedelta(days=13).total_seconds()
        if "/" in first_message:
            first_message = first_message.split("/")[6]
        if "/" in second_message:
            second_message = second_message.split("/")[6]
        start = discord.utils.snowflake_time(int(first_message))
        end = discord.utils.snowflake_time(int(second_message))
        channel = channel or ctx.channel
        if start.timestamp() > end.timestamp():
            purged = await channel.purge(after=end, before=start, check=check)
        else:
            purged = await channel.purge(after=start, before=end, check=check)

        embed = discord.Embed(title=f"✅ Successfully purged `{len(purged)}` messages from {ctx.channel.mention}",
                              color=discord.Color.brand_green())
        await channel.send(embed=embed, delete_after=5)

    @clean_between.error
    async def cleanbetween_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!clean between [msg1] [msg2] [channel]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.ChannelNotFound):
            embed = discord.Embed(title="Channel Not Found",
                                  description=f"- `{error.argument}` is not a channel.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.group(name="slowmode")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SACUL)
    async def slowmode(self, ctx:commands.Context, duration: str, channel:discord.TextChannel = None):
        await ctx.message.delete()
        channel = channel or ctx.channel
        if duration.lower() == "disable":
            if channel.slowmode_delay == 0:
                channel_embed = discord.Embed(title="An error occurred",
                                              description=f"{channel.mention} does not have any slowmode set.",
                                              color=discord.Color.brand_red(),
                                              timestamp=discord.utils.utcnow())
                await ctx.send(embed=channel_embed, delete_after=10.0)
                return
            channel_embed = discord.Embed(title=f"✅ Slowmode disabled in {channel.mention}",
                                color=discord.Color.brand_green())
            await ctx.send(embed=channel_embed, delete_after=10.0)
            await channel.edit(slowmode_delay=None)
            channel = ctx.guild.get_channel(MOD_LOG)

            embed = discord.Embed(title=f"Slowmode disabled in {channel.mention}",
                                description=f">>> **Mod:** {ctx.author.mention} ({ctx.author.id})",
                                color=discord.Color.brand_red(),
                                timestamp=discord.utils.utcnow())
            embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
            await channel.send(embed=embed)
            return
        td = datetime.timedelta()
        duration_list = [duration for duration in duration.split(",")]
        for duration in duration_list:
            if duration.endswith("s"):
                new_time = duration.strip("s")
                td += datetime.timedelta(seconds=int(new_time))
            elif duration.endswith("m"):
                new_time = duration.strip("m")
                td +=  datetime.timedelta(minutes= int(new_time))
            elif duration.endswith("h"):
                new_time = duration.strip("h")
                td +=  datetime.timedelta(hours= int(new_time))
            elif duration.endswith("hour"):
                new_time = duration.strip("hour")
                td +=  datetime.timedelta(hours= int(new_time))
            else:
                return await ctx.send(f"Invalid input: `!slowmode 30s`")

        total_seconds = int(td.total_seconds())
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        duration_message_parts = []
        if hours > 6:
            return await ctx.send(f"The max slowmode duration is 6h.", delete_after=5.0)
        if hours > 0:
            duration_message_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            duration_message_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds > 0:
            duration_message_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        duration_message = ' and '.join(duration_message_parts)
        channel_embed = discord.Embed(title=f"✅ Slowmode set to {duration_message} in {channel.mention}",
                              color=discord.Color.brand_green())
        await ctx.send(embed=channel_embed, delete_after=10.0)
        await channel.edit(slowmode_delay=total_seconds)
        channel = ctx.guild.get_channel(MOD_LOG)

        embed = discord.Embed(title=f"Slowmode set in {channel.mention}",
                              description=f">>> **Duration:** {duration_message}\n**Mod:** {ctx.author.mention} ({ctx.author.id})",
                              color=discord.Color.brand_red(),
                              timestamp=discord.utils.utcnow())
        embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
        await channel.send(embed=embed)

    @slowmode.error
    async def slowmmode_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!slowmode [duration] [channel]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.ChannelNotFound):
            embed = discord.Embed(title="Channel Not Found",
                                  description=f"- `{error.argument}` is not a channel.",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command(name="masskick")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    async def masskick(self, ctx:commands.Context, *members:discord.Member):
        await ctx.message.delete()
        embed = discord.Embed(title="Masskick",
                              description="Are you sure you want to execute this?",
                              color=discord.Color.brand_red())
        view = MassView(set(members), "masskick", self.bot, ctx.author.id)
        await ctx.send(embed=embed, view=view)

    @masskick.error
    async def masskick_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!masskick [users]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command(name="massban")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    async def massban(self, ctx:commands.Context, *users:discord.Member | discord.User):
        await ctx.message.delete()
        embed = discord.Embed(title="Massban",
                              description="Are you sure you want to execute this?",
                              color=discord.Color.brand_red())
        users_list = []
        for user in set(users):
            if isinstance(user, discord.Member):
                if user.top_role >= ctx.author.top_role:
                    continue
            users_list.append(user.id)
        if not users_list:
            embed = discord.Embed(title="An error occurred",
                                  description=f"You are unable to ban all the members given.",
                                  color=discord.Color.brand_red())
            await ctx.send(embed=embed, delete_after=10.0)
            return
        view = MassView(users_list, "massban", self.bot, ctx.author.id)
        await ctx.send(embed=embed, view=view)

    @massban.error
    async def massban_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!massban [users]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.UserNotFound):
            embed = discord.Embed(title="User Not Found",
                                  description=f"- `{error.argument}` is not a user.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command(name="massmute")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    async def massmute(self, ctx:commands.Context, *users:discord.Member):
        await ctx.message.delete()
        embed = discord.Embed(title="Massmute",
                              description="Are you sure you want to execute this?",
                              color=discord.Color.brand_red())
        view = MassView(set(users), "massmute", self.bot, ctx.author.id)
        await ctx.send(embed=embed, view=view)

    @massmute.error
    async def massmute_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!massmute [users]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command(name="massunban")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    async def massunban(self, ctx:commands.Context, *users:discord.Object):
        await ctx.message.delete()
        embed = discord.Embed(title="Massunban",
                              description="Are you sure you want to execute this?",
                              color=discord.Color.brand_red())
        users = {user.id for user in set(users)}
        view = MassView(users, "massunban", self.bot, ctx.author.id)
        await ctx.send(embed=embed, view=view)
    @massunban.error
    async def massunban_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!massunban [users]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command(name="case", aliases=["modlogs"])
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, MODERATOR, SENIOR, SACUL)
    async def case(self, ctx:commands.Context, case_id : str):
        async with self.bot.mod_pool.acquire() as conn:
            row= await conn.execute('''SELECT user_id, action, mod_id, time FROM moddb WHERE case_id = ? ''',
                               (case_id,))
            result = await row.fetchone()
        if result is None:
            embed = discord.Embed(title=f"❌ No such case: `{case_id}`",
                                  color=discord.Color.brand_red())
        else:
            try:
                user = self.bot.get_user(result["user_id"]) or await self.bot.fetch_user(result["user_id"])
            except discord.NotFound as e:
                return await ctx.send(f"An error occurred: {e}")
            try:
                mod = self.bot.get_user(result["mod_id"]) or await self.bot.fetch_user(result["mod_id"])
            except discord.NotFound as e:
                return await ctx.send(f"An error occurred: {e}")
            action : str= result["action"]
            timestamp = int(result["time"])
            embed = discord.Embed(title=f"Case Info",
                                  description=f">>> **User:** {user.mention} ({user.id})\n**Action:** {action.title()}\
                                    \n**Created on:** <t:{timestamp}:f>",
                                    color=discord.Color.blurple())
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Mod: @{mod} ({mod.id})", icon_url=mod.display_avatar.url)
        await ctx.send(embed=embed)
    @case.error
    async def case_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!case [case_id]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        else:
            embed = discord.Embed(
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @commands.group(name="caselist")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SACUL, SENIOR, MODERATOR)
    async def caselist(self, ctx:commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Invalid Input",
                                  description=f">>> - `!caselist user [user]`\n- `!caselist mod [user]`",
                                    color=discord.Color.brand_red())
            await ctx.send(embed=embed)
    @caselist.error
    async def caselist_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingAnyRole):
            return
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @caselist.command(name="user")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, MODERATOR, SENIOR, SACUL)
    async def caselist_user(self, ctx:commands.Context, user:discord.User):
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute('''SELECT case_id, action, mod_id, time FROM moddb WHERE user_id = ?
                                      ORDER BY time DESC''',
                                      (user.id,))
            results = await rows.fetchall()
        if results:
            results_per_page = 15
            data = [f"- **{result["action"].capitalize()}** by <@{result["mod_id"]}> (`{result["case_id"]}`) | <t:{int(result["time"])}:f>" for result in results]
            embeds = [
                discord.Embed(
                    title="Case list",
                    description=f">>> {'\n'.join(data[i:i + results_per_page])}"
                ).set_author(name=f"@{user} ({user.id})", icon_url=user.display_avatar.url)
                for i in range(0, len(results), results_per_page)] 
            paginator = ButtonPaginator(embeds)
            await paginator.start(ctx.channel)
        else:
            embed = discord.Embed(title=f"❌ No cases found for @{user}",
                                  color=discord.Color.brand_red())
            await ctx.send(embed=embed)
    @caselist_user.error
    async def caselistuser_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!caselist user [user]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.UserNotFound):
            embed = discord.Embed(title="User Not Found",
                                  description=f"- `{error.argument}` is not a user.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)
    @caselist.command(name="mod")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, MODERATOR, SENIOR, SACUL)
    async def caselist_mod(self, ctx:commands.Context, mod:discord.User):
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute('''SELECT case_id, user_id, action, time FROM moddb WHERE mod_id = ?
                                      ORDER BY time DESC''',
                                      (mod.id,))
            results = await rows.fetchall()
        if results:
                results_per_page = 15
                data = [f"- **{result["action"].capitalize()}** <@{result["user_id"]}> (`{result["case_id"]}`) | <t:{int(result["time"])}:f>" for result in results]
                embeds = [
                    discord.Embed(
                        title="Case List",
                        description=f">>> {'\n'.join(data[i:i + results_per_page])}"
                    ).set_footer(text=f"Mod: @{mod} ({mod.id})", icon_url=mod.display_avatar.url)
                    for i in range(0, len(results), results_per_page)] 
                paginator = ButtonPaginator(embeds)
                await paginator.start(ctx.channel)
        else:
            embed = discord.Embed(title=f"❌ No cases found for moderator: @{mod}",
                                  color=discord.Color.brand_red())
            await ctx.send(embed=embed)

    @caselist_mod.error
    async def caselistmod_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!caselist mod [user]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.argument}` is not a member.",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.UserNotFound):
            embed = discord.Embed(title="User Not Found",
                                  description=f"- `{error.argument}` is not a user.",
                                    color=discord.Color.brand_red())
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @commands.command(name="deletecase")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN, SACUL)
    async def deletecase(self, ctx:commands.Context, case_id :str) -> None:
        await ctx.message.delete()
        async with self.bot.mod_pool.acquire() as conn:
            row = await conn.execute('''SELECT NULL FROM moddb WHERE case_id = ?''',
                               (case_id,))
            result = await row.fetchone()
            if result:
                await conn.execute('''DELETE FROM moddb WHERE case_id  =?''',
                                   (case_id,))
        if result:
            embed = discord.Embed(title=f"✅ Successfully deleted case `{case_id}`",
                                  color=discord.Color.brand_green())
            log_embed = discord.Embed(title=f"Case deleted `{case_id}`",
                                      description=f"- Deleted by {ctx.author.mention} ({ctx.author.id})",
                                      color=discord.Color.brand_red(),
                                      timestamp=discord.utils.utcnow())
            log_embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
            channel = ctx.guild.get_channel(MOD_LOG)
            await channel.send(embed=log_embed)
        else:
            embed = discord.Embed(title=f"❌ There is no such case_id `{case_id}`",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

    @caselist_user.error
    async def caselistuser_error(self, ctx:commands.Context, error:commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Invalid Input",
                                  description=f"\n- `!deletecase [case_id]`",
                                    color=discord.Color.brand_red())
        elif isinstance(error, commands.MissingAnyRole):
            return
        else:
            embed = discord.Embed(title="An Error Occurred",
                                  description=f"- {error}",
                                  color=discord.Color.brand_red())
        await ctx.send(embed=embed)

async def setup(bot:commands.Bot): 
    await bot.add_cog(ModCog(bot))

class MassView(discord.ui.View):
    def __init__(self, users : list[discord.Object | discord.User | discord.Member], action:str, bot:commands.Bot, mod_id : int):
        super().__init__(timeout=900)
        self.users = users
        self.action = action
        self.bot = bot
        self.mod_id = mod_id
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="MassPunish")
    async def callback(self, interaction:discord.Interaction, button:discord.ui.Button):
        if self.action == "massban":
            await interaction.response.send_modal(MassBanModal(self.users, self.bot))
        elif self.action == "massmute":
            await interaction.response.send_modal(MassMuteModal(self.users, self.bot))
        elif self.action == "massunban":
            await interaction.response.send_modal(MassUnbanModal(self.users, self.bot))
        elif self.action == "masskick":
            await interaction.response.send_modal(MassKickModal(self.users, self.bot))
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="CancelMassPunish")
    async def callback2(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.message.delete()

    async def interaction_check(self, interaction:discord.Interaction):
        return interaction.user.id == self.mod_id

class MassBanModal(discord.ui.Modal):
    def __init__(self, users: list[discord.Object], bot:commands.Bot):
        super().__init__(title="Massban", timeout=900, custom_id="Massban")
        self.actual_users = users
        print(self.actual_users)
        self.users_split = ",".join(str(user_id) for user_id in users)
        self.users = discord.ui.TextInput(label="Users", default=self.users_split, required=True, min_length=18, max_length=1000,
                                                style=discord.TextStyle.long)
        self.reason = discord.ui.TextInput(label="Reason", placeholder="The reason for the massban", default="No reason provided.",
                                           required=False, min_length=1, max_length=1000, style=discord.TextStyle.long)
        self.add_item(self.users)
        self.add_item(self.reason)
        self.bot =bot
    async def on_submit(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Now attempting to ban the users... This might take a while", ephemeral=True)
        if self.users_split != self.users.value:
            to_ban = []
            for user_id in self.users.value.split(","):
                try:
                    member = interaction.guild.get_member(int(user_id)) or await interaction.guild.fetch_member(int(user_id))
                    if member:
                        if member.top_role >= interaction.user.top_role:
                            continue
                except discord.NotFound:
                    pass
                to_ban.append(discord.Object(user_id))
        else:
            print("No change")
            to_ban = [discord.Object(user_id) for user_id in self.users.value.split(",")]
        try:
            result = await interaction.guild.bulk_ban(to_ban, reason=f"Banned by {interaction.user} for: {self.reason.value}")
            if result.banned:
                banned  = []
                insert_value = []
                for user in result.banned:
                    case_id = convert_to_base64()
                    banned.append(f"{user.id} | `{case_id}`")
                    insert_value.append((case_id, user.id, "ban", interaction.user.id, time.time()))

        except discord.HTTPException as e:
            return await interaction.followup.send(f"An error occurred: {e}")
        response_embed = discord.Embed(title=f"{f"✅ Successfully massbanned {len(result.banned)}"}/{len(self.users.value.split(","))} users" if result.banned else f"❌ Failed to massban all users.",
                                       color=discord.Color.brand_green() if result.banned else discord.Color.brand_red())
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        await interaction.message.delete()

        if result.banned:
            channel = interaction.guild.get_channel(MOD_LOG)
            embed = discord.Embed(title=f"Massbanned [{len(result.banned)}]",
                                description=f">>> - {"\n- ".join(banned)}",
                                color=discord.Color.brand_red(),
                                timestamp=discord.utils.utcnow())
            embed.add_field(name=f"Banned by",
                            value=f">>> {interaction.user.mention} ({interaction.user.id})", inline=False)
            embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
            await channel.send(embed=embed)

            async with self.bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(f'''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                                        (*insert_value,))


class MassMuteModal(discord.ui.Modal):
    def __init__(self, users: list[discord.Member], bot:commands.Bot):
        super().__init__(title="Massmute", timeout=900, custom_id="Massmute")
        self.actual_users = users
        self.users_split = ",".join(str(user.id) for user in users)
        self.users = discord.ui.TextInput(label="Users", default=self.users_split, required=True, min_length=18, max_length=1000,
                                                style=discord.TextStyle.long)
        self.duration = discord.ui.TextInput(label="Duration", placeholder="The length of the mute, e.g: 3h, 5d,10m", style=discord.TextStyle.short,
                                             required=True, max_length=20, min_length=2)
        self.reason = discord.ui.TextInput(label="Reason", placeholder="The reason for the massban", default="No reason provided.",
                                           required=False, min_length=1, max_length=1000, style=discord.TextStyle.long)
        self.add_item(self.users)
        self.add_item(self.duration)
        self.add_item(self.reason)
        self.bot =bot
    async def on_submit(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Now attempting to mute the users... This might take a while", ephemeral=True)
        td = datetime.timedelta()
        duration_list = [duration for duration in self.duration.value.split(",")]
        for duration in duration_list:
            if duration.endswith("s"):
                new_time = duration.strip("s")
                td += datetime.timedelta(seconds=int(new_time))
            elif duration.endswith("m"):
                new_time = duration.strip("m")
                td +=  datetime.timedelta(minutes= int(new_time))
            elif duration.endswith("h"):
                new_time = duration.strip("h")
                td +=  datetime.timedelta(hours= int(new_time))
            elif duration.endswith("hour"):
                new_time = duration.strip("hour")
                td +=  datetime.timedelta(hours= int(new_time))
            elif duration.endswith("d"):
                new_time = duration.strip("d")
                td +=  datetime.timedelta(days= int(new_time))
            else:
                return await interaction.followup.send(f"Invalid duration: `3h` or `10m,5d`", ephemeral=True)
        total_seconds = int(td.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if days > 28:
            return await interaction.followup.send("The maximum mute time is 28 days. Please set a mute time below it.", ephemeral=True)
        duration_message_parts = []
        if days > 0:
            duration_message_parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            duration_message_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            duration_message_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds > 0:
            duration_message_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        duration_message = ' and '.join(duration_message_parts)
        user_embed = discord.Embed(title="You have been muted",
                                   description=f">>> **Duration:** {duration_message}\n**Reason:** {self.reason.value}",
                                   timestamp=discord.utils.utcnow(),
                                   color=discord.Color.brand_red())
        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        muted = []
        insert_value = []
        if [self.users_split] != self.users.value:
            for member_id in self.users.value.split(","):
                try:
                    member = interaction.guild.get_member(member_id) or await interaction.guild.fetch_member(member_id)
                except discord.NotFound:
                    continue
                if member.is_timed_out():
                    continue
                if member.guild_permissions.administrator:
                    continue
                if member.top_role >= interaction.user.top_role:
                    continue
                try:
                    await member.timeout(td, reason=f"Muted by {interaction.user} for: {self.reason.value}")
                except discord.Forbidden:
                    continue
                case_id = convert_to_base64()
                muted.append(f"{member.id} | `{case_id}`")
                insert_value.append((case_id, member.id, "mute", interaction.user.id, time.time()))
                if not member.bot:
                    try:
                        await member.send(embed=user_embed)
                    except discord.Forbidden:
                        pass
        else:
            for user in self.actual_users:
                if user.is_timed_out():
                    continue
                if user.top_role >= interaction.user.top_role:
                    continue
                if user.guild_permissions.administrator:
                    continue
                try:
                    await user.timeout(td, reason=f"Muted by {interaction.user} for: {self.reason.value}")
                except discord.Forbidden:
                    continue
                case_id = convert_to_base64()
                muted.append(f"{user.id} | `{case_id}`")
                insert_value.append((case_id, user.id, "mute", interaction.user.id, time.time()))
                if not user.bot:
                    try:
                        await user.send(embed=user_embed)
                    except discord.Forbidden:
                        pass
        response_embed = discord.Embed(title=f"✅ Successfully massmuted {len(muted)}/{len(self.users.value.split(","))}!" if muted else f"❌ Failed to massmute all the users.",
                                       color=discord.Color.brand_green() if muted else discord.Color.brand_red())
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        await interaction.message.delete()

        if muted:
            channel = interaction.guild.get_channel(MOD_LOG)
            embed = discord.Embed(title=f"Massmuted [{len(muted)}] | {duration_message}",
                                description=f">>> - {"\n- ".join(muted)}",
                                color=discord.Color.brand_red(),
                                timestamp=discord.utils.utcnow())
            embed.add_field(name=f"Muted by",
                            value=f">>> {interaction.user.mention} ({interaction.user.id})", inline=False)
            embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
            await channel.send(embed=embed)

            async with self.bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(f'''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                                        (*insert_value,))

class MassUnbanModal(discord.ui.Modal):
    def __init__(self, users: list[discord.Object], bot:commands.Bot):
        super().__init__(title="Massunban", timeout=900, custom_id="Massunban")
        users_split = ",".join(str(user_id) for user_id in users)
        self.users = discord.ui.TextInput(label="Users", default=users_split, required=True, min_length=18, max_length=1000,
                                                style=discord.TextStyle.long)
        self.reason = discord.ui.TextInput(label="Reason", placeholder="The reason for the massunban", default="No reason provided.",
                                           required=False, min_length=1, max_length=1000, style=discord.TextStyle.long)
        self.add_item(self.users)
        self.add_item(self.reason)
        self.bot =bot
    async def on_submit(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Now attempting to unban the users... This might take a while", ephemeral=True)
        unbanned = []
        insert_value = []
        to_unban = [user_id for user_id in self.users.value.split(",") if int(user_id) in [ban.user.id async for ban in interaction.guild.bans()]]
        for user_id in to_unban:
            case_id = convert_to_base64()
            unbanned.append(f"{user_id} | `{case_id}`")
            insert_value.append((case_id, int(user_id), "unban", interaction.user.id, time.time()))
            await interaction.guild.unban(discord.Object(int(user_id)), reason=f"Unbanned by {interaction.user} for: {self.reason.value}")

        response_embed = discord.Embed(title=f"{f"✅ Successfully unbanned {len(unbanned)}/{len(self.users.value.split(","))}"} users" if unbanned else f"❌ Failed to massunban all the users.",
                                        color=discord.Color.brand_green() if unbanned else discord.Color.brand_red())
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        await interaction.message.delete()

        if unbanned:
            channel = interaction.guild.get_channel(MOD_LOG)
            embed = discord.Embed(title=f"Massunbanned [{len(unbanned)}]",
                                description=f">>> - {"\n- ".join(unbanned)}",
                                color=discord.Color.brand_green(),
                                timestamp=discord.utils.utcnow())
            embed.add_field(name=f"Unbanned by",
                            value=f">>> {interaction.user.mention} ({interaction.user.id})", inline=False)
            embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
            await channel.send(embed=embed)

            async with self.bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(f'''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                                        (*insert_value,))
                    
class MassKickModal(discord.ui.Modal):
    def __init__(self, users: list[discord.Member], bot:commands.Bot):
        super().__init__(title="Masskick", timeout=900, custom_id="Masskick")
        self.actual_users = users
        self.users_split = ",".join(str(user.id) for user in users)
        self.users = discord.ui.TextInput(label="Users", default=self.users_split, required=True, min_length=18, max_length=1000,
                                                style=discord.TextStyle.long)
        self.reason = discord.ui.TextInput(label="Reason", placeholder="The reason for the massban", default="No reason provided.",
                                           required=False, min_length=1, max_length=1000, style=discord.TextStyle.long)
        self.add_item(self.users)
        self.add_item(self.reason)
        self.bot =bot
    async def on_submit(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Now attempting to kick the users... This might take a while", ephemeral=True)
        user_embed = discord.Embed(title="You have been muted",
                                   description=f">>> **Reason:** {self.reason.value}",
                                   timestamp=discord.utils.utcnow(),
                                   color=discord.Color.brand_red())
        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        kicked = []
        insert_value = []
        if self.users_split != self.users.value:
            for member_id in self.users.value.split(","):
                try:
                    member = interaction.guild.get_member(member_id) or await interaction.guild.fetch_member(member_id)
                except discord.NotFound:
                    continue
                if member.top_role >= interaction.user.top_role:
                    continue
                if not member.bot:
                    user_embed = discord.Embed(title="You have been kicked",
                                               description=f">>> **Reason:** {self.reason.value}",
                                               color=discord.Color.brand_red(),
                                               timestamp=discord.utils.utcnow())
                    user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
                    user_embed.set_thumbnail(url=interaction.guild.icon.url)
                    try:
                        await member.send(embed=user_embed)
                    except discord.Forbidden:
                        pass
                try:
                    await interaction.guild.kick(user, reason=f"Kicked by {interaction.user} for: {self.reason.value}")
                except discord.Forbidden:
                    continue
                case_id = convert_to_base64()
                kicked.append(f"{member.id} | `{case_id}`")
                insert_value.append((case_id, member.id, "kick", interaction.user.id, time.time()))

        else:
            for user in self.actual_users:
                if user.top_role >= interaction.user.top_role:
                    continue
                if not user.bot:
                    user_embed = discord.Embed(title="You have been kicked",
                                               description=f">>> **Reason:** {self.reason.value}",
                                               color=discord.Color.brand_red(),
                                               timestamp=discord.utils.utcnow())
                    user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
                    user_embed.set_thumbnail(url=interaction.guild.icon.url)
                    try:
                        await user.send(embed=user_embed)
                    except discord.Forbidden:
                        pass
                try:
                    await interaction.guild.kick(user, reason=f"Kicked by {interaction.user} for: {self.reason.value}")
                except discord.Forbidden:
                    continue
                case_id = convert_to_base64()
                kicked.append(f"{user.id} | `{case_id}`")
                insert_value.append((case_id, user.id, "kick", interaction.user.id, time.time()))
        response_embed = discord.Embed(title=f"✅ Successfully masskicked {len(kicked)}/{len(self.users.value.split(","))}!" if kicked else f"❌ Failed to masskick all the users.",
                                       color=discord.Color.brand_green() if kicked else discord.Color.brand_red())
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        await interaction.message.delete()

        if kicked:
            channel = interaction.guild.get_channel(MOD_LOG)
            embed = discord.Embed(title=f"Masskicked [{len(kicked)}]",
                                description=f">>> - {"\n- ".join(kicked)}",
                                color=discord.Color.brand_red(),
                                timestamp=discord.utils.utcnow())
            embed.add_field(name=f"Kicked by",
                            value=f">>> {interaction.user.mention} ({interaction.user.id})", inline=False)
            embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
            await channel.send(embed=embed)

            async with self.bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(f'''INSERT INTO moddb (case_id, user_id, action, mod_id, time) VALUES (?, ?, ?, ?, ?)''',
                                        (*insert_value,))

class AppealView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Appeal", style=discord.ButtonStyle.link, url="https://discord.gg/er2ErWNZjG"))
class PreviousCase(discord.ui.View):
    def __init__(self, message_id:int):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Tempban Case", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{GUILD_ID}/{MOD_LOG}/{message_id}"))
