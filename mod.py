import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import time
import os
import random
import string

MOD_LOG = 1294290963971178587
NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
MODERATOR = 1319214233803816960
SENIOR = 1343556008223707156
ADMIN = (1319213465390284860, 1343556153657004074, 1356640586123448501, 1343579448020308008)
SACUL = 1294291057437048843

class ModCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    async def handle_warns(self, ctx:commands.Context, member:discord.Member, warns:int, case_id : str, reason:str) -> None:
        channel = ctx.guild.get_channel(MOD_LOG)
        if warns > 9:
            user_embed = discord.Embed(title="You have been auto banned (10 warns or more)",
                            description=f">>>**Duration:** Permanent\
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
            try:
                await ctx.guild.ban(member, reason=f"Auto Banned (10 warns) by {ctx.author} for: {reason}")
            except discord.Forbidden as e:
                await ctx.send(f"An error occurred: {e}")
                return
            
            embed = discord.Embed(title=f"Auto Banned | 10 warns (`{case_id}`)",
                                description=f">>> **User:** {member.mention} ({member.id})\
                                    \n**Duration:** Permanent\n**Reason:** {reason}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            embed.add_field(name=f"Banned by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
            embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
            embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            async with self.bot.mod_pool.acquire() as conn:
                await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?)''',
                                   (case_id, member.id, "ban", ctx.author.id))
                await conn.commit()
            await channel.send(embed=embed)
        elif warns == 8:
            try:
                await member.timeout(datetime.timedelta(days=1), reason=f"Auto muted (8warns) by {ctx.author} for: {reason}")
            except discord.Forbidden as e:
                return await ctx.send(f"An error occurred: {e}")
            user_embed = discord.Embed(title="You have been auto muted (8 warns)",
                            description=f">>>**Duration:** 1d\
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
            
            embed = discord.Embed(title=f"Auto Muted | 8 warns (`{case_id}`)",
                                description=f">>> **User:** {member.mention} ({member.id})\
                                    \n**Duration:** 1d\n**Reason:** {reason}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            embed.add_field(name=f"Muted by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
            embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
            embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        elif warns == 5:
            try:
                await member.timeout(datetime.timedelta(hours=6), reason=f"Auto muted (8warns) by {ctx.author} for: {reason}")
            except discord.Forbidden as e:
                return await ctx.send(f"An error occurred: {e}")
            user_embed = discord.Embed(title="You have been auto muted (8 warns)",
                            description=f">>>**Duration:** 6h\
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

            
            embed = discord.Embed(title=f"Auto Muted | 5 warns (`{case_id}`)",
                                description=f">>> **User:** {member.mention} ({member.id})\
                                    \n**Duration:** 6h\n**Reason:** {reason}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            embed.add_field(name=f"Muted by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
            embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
            embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        elif warns == 2:
            user_embed = discord.Embed(title=f"Auto Formal Warn (2 warns)",
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
            
            embed = discord.Embed(title=f"Auto Formal Warn | 2 warns (`{case_id}`)",
                                description=f">>> **User:** {member.mention} ({member.id}) \n**Reason:** {reason}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
            embed.add_field(name=f"Warned by", value=f">>> {ctx.author.mention} ({ctx.author.id})")
            embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
            embed.set_footer(text=f"@{ctx.author}", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        if warns < 10:
            async with self.bot.mod_pool.acquire() as conn:
                await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?)''',
                                   (case_id, member.id, "warn", ctx.author.id))
                await conn.commit()

    @commands.command()
    @commands.has_any_role(*ADMIN, MODERATOR, SACUL, SENIOR)
    async def warn(self, ctx:commands.Context, member:discord.Member,  *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(f"You cannot warn a member who's role is higher or equal to yours.")
        case_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        async with self.bot.mod_pool.acquire() as conn:
            row = await conn.execute('''SELECT case_id FROM moddb WHERE user_id =? AND action = ?''',
                            (member.id, "warn"))
            result = await row.fetchall()
        results = [f"{item["case_id"]}" for item in result]
        if result is not None:
            if len(result) + 1> 1 :
                await self.handle_warns(ctx, member, len(result) + 1, case_id, reason)
                return

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
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?)''',
                               (case_id, member.id, "warn", ctx.author.id))
            await conn.commit()
    @commands.command()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx:commands.Context, member : discord.Member | discord.User, duration : str = "Permanent", *, reason:str = "No reason provided.") -> None:
        await ctx.message.delete()
        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                return await ctx.send(f"You cannot ban a member who's role is higher or same as yours.", delete_after=5)
        elif isinstance(member, discord.User):
            async for entry in ctx.guild.bans():
                if entry.user.id == member.id:
                    await ctx.send(f"{member.mention} is already banned!", delete_after=5)
                    return
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
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass
        try:
            await ctx.guild.ban(member, reason=f"Banned by {ctx.author} for: {final_reason}")
        except discord.Forbidden as e:
            return await ctx.send(f"An error occurred: {e}", 
                                delete_after=5.0)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
        channel = ctx.guild.get_channel(MOD_LOG)
        case_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

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
        await channel.send(embed=embed)

        async with self.bot.mod_pool.acquire() as conn:
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?) ''',
                               (case_id, member.id, f"{"ban" if not total_seconds else "tempban"}", ctx.author.id))

            if total_seconds:
                await conn.execute('''INSERT INTO tempbandb (user_id, time) VALUES (?, ?)
                                    ON CONFLICT(user_id) DO UPDATE SET time=excluded.time''',
                                    (member.id, (td.total_seconds() + time.time())))
            await conn.commit()

    @commands.command()
    @commands.has_any_role(*ADMIN, SENIOR, SACUL)
    async def unban(self, ctx:commands.Context, user:discord.User, *, reason:str="No reason provided."):
        await ctx.message.delete()
        bans = [entry.user.id async for entry in ctx.guild.bans()]
        if user.id not in bans:
            return await ctx.send(f"{user} is not banned!", delete_after=5.0)
        try:
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author} for: {reason}")
        except discord.Forbidden as e:
            return await ctx.send(f"<@802167689011134474> An error occurred: {e}")

        user_embed = discord.Embed(title="You have been ubanned",
                            description=f">>>**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())
        
        user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        user_embed.set_thumbnail(url=ctx.guild.icon.url)
        case_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
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
                
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?)''',
                               (case_id, user.id, "unban", ctx.author.id))
            await conn.commit()

    @commands.command()
    @commands.has_any_role(*ADMIN, SACUL, SENIOR)
    async def kick(self, ctx:commands.Context, member:discord.Member,  *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(f"You cannot kick a member who's role is higher or equal to yours.")
        case_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

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
            return await ctx.send(f"An error occurred: {e}")
        channel = ctx.guild.get_channel(MOD_LOG)
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
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?)''',
                            (case_id, member.id, "kick", ctx.author.id))
            await conn.commit()

    @commands.command()
    @commands.has_any_role(*ADMIN, SENIOR, MODERATOR, SACUL)
    async def mute(self, ctx:commands.Context, member:discord.Member, duration:str, *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(f"You cannot mute a member who's role is higher or equal to yours.", delete_after=5.0)
        elif member.guild_permissions.administrator:
            return await ctx.send(f"You cannot mute an admin!", delete_after=5.0)
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
                return await ctx.send(f"Invalid input: `!mute @user 3h` or `!mute @user 10m,5d`")

        total_seconds = int(td.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if days > 28:
            return await ctx.send("The maximum mute time is 28 days. Please set a mute time below it.", delete_after=5)
        try:
            await member.timeout(td, reason=f"Muted by {ctx.author} for: {reason}")
        except discord.Forbidden as e:
            return await ctx.send(f"<@802167689011134474> An error occurred: {e}")
        case_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
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
                            description=f">>>**Duration:** {duration_message}\
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
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?)''',
                               (case_id, member.id, "mute", ctx.author.id))
            await conn.commit()

    @commands.command()
    @commands.has_any_role(*ADMIN, SENIOR, MODERATOR, SACUL)
    async def unmute(self, ctx:commands.Context, member:discord.Member, *, reason:str="No reason provided."):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(f"You cannot unmute a member who's role is higher or equal to yours.", delete_after=5.0)
        elif not member.is_timed_out():
            return await ctx.send(f"{member} is not timed out!", delete_after=5.0)
        try:
            await member.timeout(None, reason=reason)
        except discord.Forbidden as e:
            return await ctx.send(f"<@802167689011134474> An error occurred: {e}")

        user_embed = discord.Embed(title="You have been unmuted",
                            description=f">>>**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())
        
        user_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        user_embed.set_thumbnail(url=ctx.guild.icon.url)
        if not member.bot:
            try:
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass
        case_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
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
            await conn.execute('''INSERT INTO moddb (case_id, user_id, action, mod_id) VALUES (?, ?, ?, ?)''',
                               (case_id, member.id, "unmute", ctx.author.id))
            await conn.commit()

    @commands.group(name="clean", invoke_without_command=True)
    async def clean(self, ctx:commands.Context, limit : int, channel : discord.TextChannel | None = None) -> None:
        if limit > 800:
            return await ctx.send(f"You can only purge up to a limit of `800` messages.", delete_after=5.0)
        def check(msg:discord.Message):
            return int(time.time() - msg.created_at.timestamp()) < datetime.timedelta(days=13).total_seconds()
        channel = channel or ctx.channel
        purged = await channel.purge(limit=limit, check=check)
        embed = discord.Embed(title=f"✅ Successfully purged `{len(purged)}` messages from {channel.mention}",
                              color=discord.Color.brand_green())
        await channel.send(embed=embed, delete_after=5)


    @clean.command(name="until")
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

    @clean.command(name="between")
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
        purged = await channel.purge(after=end, before=start, check=check)
        embed = discord.Embed(title=f"✅ Successfully purged `{len(purged)}` messages from {ctx.channel.mention}",
                              color=discord.Color.brand_green())
        await channel.send(embed=embed, delete_after=5)


async def setup(bot:commands.Bot):
    await bot.add_cog(ModCog(bot))
