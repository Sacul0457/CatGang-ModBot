from __future__ import annotations

import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.utils import MISSING
import datetime
import time
from paginator import ButtonPaginator
from functions import save_to_moddb, double_query, convert_to_base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import ModBot


class ModCog(commands.Cog):
    def __init__(self, bot: ModBot):
        self.bot = bot
    
    clean_command = app_commands.Group(name="clean", description="Purge messages")


    @staticmethod
    def has_roles(admin: bool = False, mod: bool = False, snr: bool = False, appeal_staff: bool = False):
        async def predicate(interaction: discord.Interaction[ModBot]) -> bool:
            roles = [1294291057437048843]
            if admin:
                roles.extend(interaction.client.admin)
            if mod:
                roles.extend(interaction.client.mod)
            if snr:
                roles.extend(interaction.client.senior)
            if appeal_staff:
                roles.extend(interaction.client.appeal_staff)
            return any(role_id in interaction.user._roles for role_id in roles)
        return app_commands.check(predicate)

    async def cog_load(self):
        self.auto_unban.start()

    @app_commands.command(name="resetnickname", description="Reset the nickname of a user")
    @app_commands.guild_only()
    @has_roles(admin=True, snr=True, mod=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(user = "The member to reset")
    async def resetnickname(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        if user.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"- You cannot reset a member's nickname who's role is higher than or equal to yours.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        if user.nick is None:
            embed = discord.Embed(
                title="No Nickname Set",
                description=f"- {user.mention} does not have a nickname.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        nickname = user.nick
        try:
            await user.edit(nick=None)
        except discord.Forbidden as e:
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"- {e}",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        channel_embed = discord.Embed(
            title=f"✅ Successfully reset `@{user}`'s nickname",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed, ephemeral=True)
        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title="Nickname Reset",
            description=f">>> **User:** {user.mention} ({user.id})\n**Before reset:** `{nickname}`",
            color=discord.Color.brand_red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name=f"Resetted by", value=f"{interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        await channel.send(embed=embed)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.guild_only()
    @app_commands.describe(user = "The user to warn", reason = "The reason for warning", image_proof1="The image proof",
                           image_proof2="The image proof", image_proof3="The image proof")
    @app_commands.default_permissions(manage_messages=True)
    @has_roles(admin=True, mod=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided.",
        image_proof1: discord.Attachment | None = None,
        image_proof2: discord.Attachment | None = None,
        image_proof3: discord.Attachment | None = None,
    ):
        await interaction.response.defer(ephemeral=True)
        if isinstance(user, discord.Member) and user.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"- You cannot warn a member who's role is higher than or equal to yours.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)

        files = [await image_proof1.to_file()] if image_proof1 is not None else []
        if image_proof2 is not None:
            files.append(await image_proof2.to_file())
        if image_proof3 is not None:
            files.append(await image_proof3.to_file())
        

        case_id = convert_to_base64()
        user_embed = discord.Embed(
            title="You have been warned",
            description=f">>> **Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_red(),
        )
        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)
        if not user.bot:
            try:
                await user.send(embed=user_embed, view=AppealView(), files=files)
            except discord.Forbidden:
                pass
        channel_embed = discord.Embed(
            title=f"✅ Successfully warned `@{user}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)
        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title=f"Warned (`{case_id}`)",
            description=f">>> **User:** {user.mention} ({user.id})\
                                \n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_red(),
        )

        embed.add_field(
            name=f"Warned by", value=f">>> {interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        log_message = await channel.send(embed=embed, files=files)
        await save_to_moddb(self.bot, case_id, user.id, 'warn', interaction.user.id, time.time(), log_message.id)


    @app_commands.command(name="unwarn", description="Remove a warn from a user")
    @app_commands.guild_only()
    @app_commands.describe(case_id="The case ID of the case", reason = "The reason for unwarning")
    @app_commands.default_permissions(manage_messages=True)
    @has_roles(admin=True)
    async def unwarn(
        self,
        interaction: discord.Interaction,
        case_id: str,
        reason: str = "No reason provided."
    ):
        await interaction.response.defer(ephemeral=True)
        new_case_id = convert_to_base64()
        async with self.bot.mod_pool.acquire() as conn:
            row = await conn.execute(
                """SELECT user_id, action, mod_id, time, log_id FROM moddb WHERE case_id = ? AND action = ?""",
                (case_id, "warn"),
            )
            result = await row.fetchone()
            if result is None:
                embed = discord.Embed(
                    title=f"❌ No such case: `{case_id}`", color=discord.Color.brand_red()
                )
                return await interaction.followup.send(embed=embed)
            
            await conn.execute('''DELETE FROM moddb WHERE CASE_ID = ?''',
                                (case_id, ))
            try:
                member = interaction.guild.get_member(
                    result["user_id"]
                ) or await self.bot.fetch_user(result["user_id"])
            except discord.NotFound:
                return
        if isinstance(member, discord.Member) and not member.bot:
            user_embed = discord.Embed(
                title=f"You have been unwarned (`{new_case_id}`)",
                description=f">>> **Reason:** {reason}",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_green(),
            )
            user_embed.add_field(name="Previous Case",
                                value=f">>> **Case ID:** `{case_id}`\
                                    \n**Warned on:** <t:{int(result['time'])}:f>",
                                    inline=False)

            user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
            user_embed.set_thumbnail(url=interaction.guild.icon.url)
            try:
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass
        channel_embed = discord.Embed(
            title=f"✅ Successfully unwarned `@{member}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)
        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title=f"Unwarned (`{new_case_id}`)",
            description=f">>> **User:** {member.mention} ({member.id})\
                                \n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_green(),
        )

        embed.add_field(name="Previous Case",
                                value=f">>> **Case ID:** `{case_id}`\
                                \n**Mod:** <@{result['mod_id']}> ({result['mod_id']})\
                                \n**Warned on:** <t:{int(result['time'])}:f>",
                                inline=False)
        embed.add_field(
            name=f"Unwarned by", value=f">>> {interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        log_message = await channel.send(embed=embed, view=JumpToCase(result['log_id'], self.bot.main_guild_id, self.bot.mod_log))
        await save_to_moddb(self.bot, new_case_id, result["user_id"], "unwarn", interaction.user.id, time.time(), log_message.id)


    @app_commands.command(name="deletewarns", description="Delete/Remove all warns from a user")
    @app_commands.guild_only()
    @app_commands.describe(user = "The user to delete warns from", reason = "The reason for deleting all warns")
    @app_commands.default_permissions(manage_messages=True)
    @has_roles(admin=True)
    async def deletewarns(
        self,
        interaction: discord.Interaction,
        user: discord.Member | discord.User,
        reason: str = "No reason provided."
    ):
        await interaction.response.defer(ephemeral=True)
        if isinstance(user, discord.Member) and user.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"- You cannot remove a member's warns who's role is higher than or equal to yours.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute(
                """SELECT case_id FROM moddb WHERE user_id = ? AND action = ?""",
                (user.id, "warn"),
            )
            results = await rows.fetchall()
            if not results:
                embed = discord.Embed(
                    title="No Warns Found",
                    description=f"{user.mention} has no warns.",
                    color=discord.Color.brand_red(),
                )
                return await interaction.followup.send(embed=embed)
            case_ids = [result["case_id"] for result in results]
            case_id = convert_to_base64()
            await conn.execute(
                f"""DELETE FROM moddb WHERE case_id IN ({",".join("?" for _ in case_ids)})""",
                tuple(case_ids),
            )

            await conn.commit()
        if isinstance(user, discord.Member) and not user.bot:
            user_embed = discord.Embed(
                title="All your warns have been removed",
                description=f">>> **Reason:** {reason}",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_green(),
            )

            user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
            user_embed.set_thumbnail(url=interaction.guild.icon.url)
            if not user.bot:
                try:
                    await user.send(embed=user_embed)
                except discord.Forbidden:
                    pass
        channel_embed = discord.Embed(
            title=f"✅ Successfully deleted all warns for `@{user}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)
        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title=f"Warns Deleted (`{case_id}`)",
            description=f">>> **User:** {user.mention} ({user.id})\
                                \n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_green(),
        )

        embed.add_field(
            name=f"Unwarned by", value=f">>> {interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        await channel.send(embed=embed)


    @tasks.loop(seconds=30)
    async def auto_unban(self):
        async with self.bot.mod_pool.acquire() as conn:
            row = await conn.execute(
                """SELECT user_id, time, log_id FROM tempbandb
                               ORDER BY time ASC
                               LIMIT 1"""
            )
            result = await row.fetchone()
            if result:
                user_id = result["user_id"]
                row2 = await conn.execute(
                    """SELECT case_id, mod_id, time FROM moddb WHERE user_id = ? AND action = ?""",
                    (user_id, "tempban"),
                )
                case_data = await row2.fetchone()
        if not result:
            self.auto_unban.cancel()
            return
        to_sleep_timestamp = result["time"]
        to_sleep = datetime.datetime.fromtimestamp(to_sleep_timestamp)
        await discord.utils.sleep_until(to_sleep)

        user = self.bot.get_user(int(user_id)) or discord.Object(int(user_id), type=discord.User)

        mod = self.bot.get_user(case_data["mod_id"]) or discord.Object(case_data['mod_id'], type=discord.User)

        guild = self.bot.get_guild(self.bot.main_guild_id)
        try:
            await guild.unban(user, reason=f"Tempban Expired")
        except discord.Forbidden:
            return
        banned_on = case_data["time"]
        channel = self.bot.get_channel(self.bot.mod_log)
        log_id = result["log_id"]
        old_case_id = result['case_id']
        case_id = convert_to_base64()
        embed = discord.Embed(
            title=f"Unbanned | Tempban Expired (`{case_id}`)",
            description=f">>> **User:** <@{user.id}> ({user.id})\n**Case Id:** `{old_case_id}`\
                                \n**Mod:** <@{mod.id}> ({mod.id})\n**Banned on:** <t:{int(banned_on)}:f>",
            color=discord.Color.brand_green(),
            timestamp=discord.utils.utcnow(),
        )
        if isinstance(user, discord.User):
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
        if isinstance(mod, discord.User):
            embed.set_footer(text=f"@{mod}", icon_url=mod.display_avatar.url)
        log_message = await channel.send(embed=embed, view=PreviousCase(log_id, self.bot.main_guild_id, self.bot.mod_log))
        await double_query(self.bot, query_one='''DELETE FROM tempbandb WHERE user_id = ?''', 
                            value_one=(user_id, ),

                            query_two='''INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)''',
                            value_two=(case_id, user_id, "unban", mod.id, time.time(), log_message.id))


    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.guild_only()
    @has_roles(admin=True, snr=True, mod=True)
    @app_commands.describe(user = "The user to ban", duration="The duration of the ban, else Permanent", 
                           reason = "The reason for banning", image_proof1="The image proof",
                           image_proof2="The image proof", image_proof3="The image proof")
    @app_commands.default_permissions(manage_messages=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member | discord.User,
        duration: str | None = None,
        reason: str = "No reason provided.",
        image_proof1: discord.Attachment | None = None,
        image_proof2: discord.Attachment | None = None,
        image_proof3: discord.Attachment | None = None,

    ) -> None:
        
        await interaction.response.defer(ephemeral=True)
        td = datetime.timedelta()
        total_seconds = None
        if duration is not None:
            if duration.endswith(("s", "m", "h", "d")) and any(
                num in duration for num in self.bot.numbers
            ):
                duration_list = [duration for duration in duration.split(",")]
                for duration in duration_list:
                    if duration.endswith("s"):
                        new_time = duration.strip("s")
                        td += datetime.timedelta(seconds=int(new_time))
                    elif duration.endswith("m"):
                        new_time = duration.strip("m")
                        td += datetime.timedelta(minutes=int(new_time))
                    elif duration.endswith("h"):
                        new_time = duration.strip("h")
                        td += datetime.timedelta(hours=int(new_time))
                    elif duration.endswith("hour"):
                        new_time = duration.strip("hour")
                        td += datetime.timedelta(hours=int(new_time))
                    elif duration.endswith("d"):
                        new_time = duration.strip("d")
                        td += datetime.timedelta(days=int(new_time))

                total_seconds = int(td.total_seconds() + time.time())
        
        if total_seconds is not None:
            total_seconds_duration = int(td.total_seconds())
            days = total_seconds_duration // 86400
            hours = (total_seconds_duration % 86400) // 3600
            minutes = (total_seconds_duration % 3600) // 60
            seconds = total_seconds_duration % 60
            duration_message_parts = []
            if days > 0:
                duration_message_parts.append(f"{days} day{'s' if days > 1 else ''}")
            if hours > 0:
                duration_message_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                duration_message_parts.append(
                    f"{minutes} minute{'s' if minutes > 1 else ''}"
                )
            if seconds > 0:
                duration_message_parts.append(
                    f"{seconds} second{'s' if seconds != 1 else ''}"
                )
            duration_message = " and ".join(duration_message_parts)
        final_duration = (
            f"**Duration:** Permanent"
            if not total_seconds
            else f"**Unbanned:** <t:{total_seconds}:R> ({duration_message})"
        )


        if isinstance(user, discord.Member) and user.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"- You cannot ban a member who's role is higher than or equal to yours.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)

        elif isinstance(user, discord.User):
            try:
                await interaction.guild.fetch_ban(user)
                embed = discord.Embed(
                    title="Already Banned",
                    description=f"- {user.mention} is already banned.",
                    color=discord.Color.brand_red(),
                )
                return await interaction.followup.send(embed=embed)
            except discord.NotFound:
                pass

        files = [await image_proof1.to_file()] if image_proof1 is not None else []
        if image_proof2 is not None:
            files.append(await image_proof2.to_file())
        if image_proof3 is not None:
            files.append(await image_proof3.to_file())

        if isinstance(user, discord.Member) and not user.bot:
            user_embed = discord.Embed(
                title="You have been banned",
                description=f">>> {final_duration}\
                                    \n**Reason:** {reason}",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.brand_red(),
            )

            user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
            user_embed.set_thumbnail(url=interaction.guild.icon.url)
            try:
                await user.send(embed=user_embed, view=AppealView(), files=files)
            except discord.Forbidden:
                pass
        try:
            await interaction.guild.ban(
                user, reason=f"Banned by {interaction.user} for: {reason}"
            )
        except discord.Forbidden as e:
            embed = discord.Embed(
                title="An error occurred",
                description=f"- {e}",
                color=discord.Color.red(),
            )
            return await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="An error occurred",
                description=f"- {e}\n- Command: `{interaction.message.content}`",
                color=discord.Color.red(),
            )
            return await interaction.followup.send(embed=embed)

        channel_embed = discord.Embed(
            title=f"✅ Successfully banned `@{user}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)

        channel = interaction.guild.get_channel(self.bot.mod_log)
        case_id = convert_to_base64()

        embed = discord.Embed(
            title=f"Banned (`{case_id}`)",
            description=f">>> **User:** {user.mention} ({user.id})\
                                \n{final_duration}\
                                \n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_red(),
        )
        embed.add_field(
            name=f"Banned by", value=f" >>> {interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        log_message = await channel.send(embed=embed, files=files)

        if total_seconds is not None:
            await double_query(self.bot, query_one='''INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)''',
                               value_one=(case_id, user.id, 'tempban', interaction.user.id, time.time(), log_message.id),
                               
                               query_two='''INSERT INTO tempbandb (user_id, time, log_id) VALUES (?, ?, ?)
                                    ON CONFLICT(user_id) DO UPDATE SET time=excluded.time, log_id=excluded.log_id''',
                                value_two=(user.id, (td.total_seconds() + time.time()), log_message.id))
            (
                self.auto_unban.start()
                if not self.auto_unban.is_running()
                else self.auto_unban.restart()
            )
        else:
            await save_to_moddb(self.bot, case_id, user.id, 'ban', interaction.user.id, time.time(), log_message.id)


    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.guild_only()
    @app_commands.describe(user = "The user to unban", reason = "The reason for unbanning")
    @app_commands.default_permissions(manage_messages=True)
    @has_roles(admin=True, snr=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: str = "No reason provided.",
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.guild.fetch_ban(user)
        except discord.NotFound:
            embed = discord.Embed(
                title="User Not Banned",
                description=f"- {user.mention} is not banned.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)
        try:
            await interaction.guild.unban(
                user, reason=f"Unbanned by {interaction.user} for: {reason}"
            )
        except discord.Forbidden as e:
            embed = discord.Embed(
                title="An Error Occurred ",
                description=f"- {e}",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)

        channel_embed = discord.Embed(
            title=f"✅ Successfully unbanned `@{user}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)
        case_id = convert_to_base64()
        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title=f"Unbanned (`{case_id}`)",
            description=f">>> **User:** {user.mention} ({user.id})\
                                \n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_green(),
        )

        embed.add_field(
            name=f"Unbanned by", value=f">>> {interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        log_message = await channel.send(embed=embed)
        async with self.bot.mod_pool.acquire() as conn:
            tempban_row = await conn.execute(
                """SELECT NULL FROM tempbandb WHERE user_id = ?""", (user.id,)
            )
            tempban_result = await tempban_row.fetchone()
            if tempban_result:
                await conn.execute(
                    """DELETE FROM tempbandb WHERE user_id = ?""", (user.id,)
                )

            await conn.execute(
                """INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)""",
                (case_id, user.id, "unban", interaction.user.id, time.time(), log_message.id),
            )
            await conn.commit()


    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.guild_only()
    @has_roles(admin=True, mod=True)
    @app_commands.describe(user = "The user to kick", reason = "The reason for kicking",
                            image_proof1="The image proof",
                            image_proof2="The image proof",
                            image_proof3="The image proof")
    @app_commands.default_permissions(manage_messages=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided.",
        image_proof1: discord.Attachment | None = None,
        image_proof2: discord.Attachment | None = None,
        image_proof3: discord.Attachment | None = None
    ):
        await interaction.response.defer(ephemeral=True)
        if user.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"- You cannot kick a member who's role is higher than or equal to yours.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)
        

        case_id = convert_to_base64()

        user_embed = discord.Embed(
            title="You have been kicked",
            description=f">>> **Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_red(),
        )

        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)

        files = [await image_proof1.to_file()] if image_proof1 is not None else []
        if image_proof2 is not None :
            files.append(await image_proof2.to_file())
        if image_proof3 is not None :
            files.append(await image_proof3.to_file())

        if not user.bot:
            try:
                await user.send(embed=user_embed, files=files)
            except discord.Forbidden:
                pass
        try:
            await interaction.guild.kick(user, reason=f"Kicked by {interaction.user} for {reason}")
        except discord.Forbidden as e:
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"- {e}",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)

        channel_embed = discord.Embed(
            title=f"✅ Successfully kicked `@{user}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)

        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title=f"Kicked (`{case_id}`)",
            description=f">>> **User:** {user.mention} ({user.id})\
                                \n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_red(),
        )

        embed.add_field(
            name=f"Kicked by", value=f">>> {interaction.user.mention} ({interaction.user.id})",
        inline=False)
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        log_message = await channel.send(embed=embed, files=files)
        await save_to_moddb(self.bot, case_id, user.id, 'kick', interaction.user.id, time.time(), log_message.id)


    @app_commands.command(name="mute", description="Mute a user from the server")
    @app_commands.guild_only()
    @has_roles(admin=True, snr=True, mod=True)
    @app_commands.describe(user = "The user to mute", reason = "The reason for muting", 
                           duration="The duration of the mute",
                           image_proof1="The image proof",
                           image_proof2="The image proof", 
                           image_proof3="The image proof")
    @app_commands.default_permissions(manage_messages=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        duration: str,
        reason: str = "No reason provided.",
        image_proof1: discord.Attachment | None = None,
        image_proof2: discord.Attachment | None = None,
        image_proof3: discord.Attachment | None = None
    ):
        await interaction.response.defer(ephemeral=True)
        if user.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"- You cannot mute a member who's role is higher than or equal to yours.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)
        if user.guild_permissions.administrator:
            embed = discord.Embed(
                title="Cannot Mute Administrator",
                description=f"- You cannot mute a member who has administrator permissions.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)       

        td = datetime.timedelta()
        duration_list = [duration for duration in duration.split(",")]
        for duration in duration_list:
            if duration.endswith("s"):
                new_time = duration.strip("s")
                td += datetime.timedelta(seconds=int(new_time))
            elif duration.endswith("m"):
                new_time = duration.strip("m")
                td += datetime.timedelta(minutes=int(new_time))
            elif duration.endswith("h"):
                new_time = duration.strip("h")
                td += datetime.timedelta(hours=int(new_time))
            elif duration.endswith("hour"):
                new_time = duration.strip("hour")
                td += datetime.timedelta(hours=int(new_time))
            elif duration.endswith("d"):
                new_time = duration.strip("d")
                td += datetime.timedelta(days=int(new_time))
            else:
                embed = discord.Embed(
                    title="Invalid Duration",
                    description=f"- `{duration}` is not a valid duration.",
                )
                return await interaction.followup.send(embed=embed)

        files = [await image_proof1.to_file()] if image_proof1 is not None else []
        if image_proof2 is not None :
            files.append(await image_proof2.to_file())
        if image_proof3 is not None :
            files.append(await image_proof3.to_file())

        total_seconds = int(td.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if days > 28:
            embed = discord.Embed(
                title="Invalid Duration",
                description=f"- The maximum mute time is 28 days. Please set a mute time below it.",
            )
            return await interaction.followup.send(embed=embed)
        try:
            await user.timeout(td, reason=f"Muted by {interaction.user} for: {reason}")
        except discord.Forbidden as e:
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"- {e}",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)
        case_id = convert_to_base64()
        duration_message_parts = []
        if days > 0:
            duration_message_parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            duration_message_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            duration_message_parts.append(
                f"{minutes} minute{'s' if minutes > 1 else ''}"
            )
        if seconds > 0:
            duration_message_parts.append(
                f"{seconds} second{'s' if seconds != 1 else ''}"
            )
        duration_message = " and ".join(duration_message_parts)
        user_embed = discord.Embed(
            title="You have been muted",
            description=f">>> **Duration:** {duration_message}\
                                \n**Reason:** {reason}",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red(),
        )

        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)
        if not user.bot:
            try:
                await user.send(embed=user_embed, view=AppealView(), files=files)
            except discord.Forbidden:
                pass
        channel_embed = discord.Embed(
            title=f"✅ Successfully muted `@{user}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)

        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title=f"Muted (`{case_id}`)",
            description=f">>> **User:** {user.mention} ({user.id})\
                                \n**Duration:** {duration_message}\n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_red(),
        )

        embed.add_field(
            name=f"Muted by", value=f" >>> {interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        log_message = await channel.send(embed=embed, files=files)
        await save_to_moddb(self.bot, case_id, user.id, 'mute', interaction.user.id, time.time(), log_message.id)


    @app_commands.command(name="unmute", description="Unmute a user from the server")
    @app_commands.guild_only()
    @has_roles(admin=True, snr=True, mod=True)
    @app_commands.describe(user = "The user to unmute", reason = "The reason for unmuting")
    @app_commands.default_permissions(manage_messages=True)
    async def unmute(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided.",
    ):
        await interaction.response.defer(ephemeral=True)
        if user.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"- You cannot unmute a member who's role is higher than or equal to yours.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)
        elif not user.is_timed_out():
            embed = discord.Embed(
                title="Member Not Muted",
                description=f"- {user.mention} is not muted.",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)
        try:
            await user.timeout(
                None, reason=f"Unmuted by {interaction.user} for reason: {reason}"
            )
        except discord.Forbidden as e:
            embed = discord.Embed(
                title="An error Occurred",
                description=f"- {e}",
                color=discord.Color.brand_red(),
            )
            return await interaction.followup.send(embed=embed)

        user_embed = discord.Embed(
            title="You have been unmuted",
            description=f">>> **Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_green(),
        )

        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)
        if not user.bot:
            try:
                await user.send(embed=user_embed)
            except discord.Forbidden:
                pass

        channel_embed = discord.Embed(
            title=f"✅ Successfully unmuted `@{user}`",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)

        case_id = convert_to_base64()
        channel = interaction.guild.get_channel(self.bot.mod_log)
        embed = discord.Embed(
            title=f"Unmuted (`{case_id}`)",
            description=f">>> **User:** {user.mention} ({user.id})\
                                \n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_green(),
        )

        embed.add_field(
            name=f"Unmuted by", value=f">>> {interaction.user.mention} ({interaction.user.id})"
        )
        embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        log_message = await channel.send(embed=embed)
        await save_to_moddb(self.bot, case_id, user.id, "unmute", interaction.user.id, time.time(), log_message.id)



    @clean_command.command(name="messages", description="Purge messages")
    @app_commands.guild_only()
    @app_commands.describe(limit="The number of messages to purge", channel="The channel to purge from")
    @app_commands.default_permissions(manage_messages=True)
    @has_roles(admin=True)
    async def clean(
        self,
        interaction: discord.Interaction,
        limit: app_commands.Range[int, 1, 800],
        channel: discord.TextChannel | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        def check(msg: discord.Message):
            return (
                int(time.time() - msg.created_at.timestamp())
                < datetime.timedelta(days=13).total_seconds()
            )

        channel = channel or interaction.channel
        purged = await channel.purge(limit=limit, check=check)
        embed = discord.Embed(
            title=f"✅ Successfully purged `{len(purged)}` messages from {channel.mention}",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @clean_command.command(name="until", description="Purge messages until a certain message")
    @app_commands.guild_only()
    @app_commands.describe(until="The message to purge until, use a message link")
    @app_commands.default_permissions(manage_messages=True)
    @has_roles(admin=True)
    async def clean_until(
        self,
        interaction: discord.Interaction,
        until: str,
    ):
        await interaction.response.defer(ephemeral=True)
        def check(msg: discord.Message):
            return (
                int(time.time() - msg.created_at.timestamp())
                < datetime.timedelta(days=13).total_seconds()
            )
        try:
            until_id = until.split("/")[6]
            channel_id = until.split("/")[5]
            channel = interaction.guild.get_channel(int(channel_id)) or await interaction.guild.fetch_channel(int(channel_id))
        except (IndexError, discord.NotFound) as e:
            raise e
        new_until = discord.utils.snowflake_time(int(until_id))
        purged = await channel.purge(after=new_until, check=check)
        embed = discord.Embed(
            title=f"✅ Successfully purged `{len(purged)}` messages from {channel.mention}",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


    @clean_command.command(name="between", description="Purge between two messages")
    @app_commands.guild_only()
    @app_commands.describe(first_message="First Message", second_message="Second Message")
    @app_commands.default_permissions(manage_messages=True)
    @has_roles(admin=True)
    async def clean_between(
        self,
        interaction: discord.Interaction,
        first_message: str,
        second_message: str,
    ):
        await interaction.response.defer(ephemeral=True)
        def check(msg: discord.Message):
            return (
                int(time.time() - msg.created_at.timestamp())
                < datetime.timedelta(days=13).total_seconds()
            )
        try:
            first_message_id = first_message.split("/")[6]
            second_message_id = second_message.split("/")[6]
            channel_id = first_message.split("/")[5]
            channel_id2 = second_message.split("/")[5]
            if channel_id != channel_id2:
                raise ValueError("Channel is not the same")
            channel = interaction.guild.get_channel(int(channel_id)) or await interaction.guild.fetch_channel(int(channel_id))
        except (IndexError, discord.NotFound) as e:
            raise e
        start = discord.utils.snowflake_time(int(first_message_id))
        end = discord.utils.snowflake_time(int(second_message_id))
        if start.timestamp() > end.timestamp():
            purged = await channel.purge(after=end, before=start, check=check)
        else:
            purged = await channel.purge(after=start, before=end, check=check)

        embed = discord.Embed(
            title=f"✅ Successfully purged `{len(purged)}` messages from {channel.mention}",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name="slowmode", description="Set slowmode to a channel")
    @app_commands.guild_only()
    @has_roles(admin=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(duration="The duration of the slowmode", channel="The channel to set slowmode too")
    async def slowmode(
        self, interaction: discord.Interaction, duration: str, channel: discord.TextChannel | None = None
    ):
        await interaction.response.defer(ephemeral=True)
        channel = channel if channel is not None else interaction.channel
        if duration.lower() == "disable" or duration.startswith("0"):
            if channel.slowmode_delay == 0:
                channel_embed = discord.Embed(
                    title="An error occurred",
                    description=f"{channel.mention} does not have any slowmode set.",
                    color=discord.Color.brand_red(),
                    timestamp=discord.utils.utcnow(),
                )
                return await interaction.followup.send(embed=channel_embed)
            channel_embed = discord.Embed(
                title=f"✅ Slowmode disabled in {channel.mention}",
                color=discord.Color.brand_green(),
            )
            await interaction.followup.send(embed=channel_embed)
            await channel.edit(slowmode_delay=0)
            channel = interaction.guild.get_channel(self.bot.mod_log)

            embed = discord.Embed(
                title=f"Slowmode disabled in {channel.mention}",
                description=f">>> **Mod:** {interaction.user.mention} ({interaction.user.id})",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_footer(
                text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url
            )
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
                td += datetime.timedelta(minutes=int(new_time))
            elif duration.endswith("h"):
                new_time = duration.strip("h")
                td += datetime.timedelta(hours=int(new_time))
            elif duration.endswith("hour"):
                new_time = duration.strip("hour")
                td += datetime.timedelta(hours=int(new_time))
            else:
                return await interaction.followup.send(f"Invalid input: `!slowmode 30s`")

        total_seconds = int(td.total_seconds())
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        duration_message_parts = []
        if hours > 6:
            return await interaction.followup.send(f"The max slowmode duration is 6h.")
        if hours > 0:
            duration_message_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            duration_message_parts.append(
                f"{minutes} minute{'s' if minutes > 1 else ''}"
            )
        if seconds > 0:
            duration_message_parts.append(
                f"{seconds} second{'s' if seconds != 1 else ''}"
            )
        duration_message = " and ".join(duration_message_parts)
        channel_embed = discord.Embed(
            title=f"✅ Slowmode set to {duration_message} in {channel.mention}",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)
        await channel.edit(slowmode_delay=total_seconds)
        channel = interaction.guild.get_channel(self.bot.mod_log)

        embed = discord.Embed(
            title=f"Slowmode set in {channel.mention}",
            description=f">>> **Duration:** {duration_message}\n**Mod:** {interaction.user.mention} ({interaction.user.id})",
            color=discord.Color.brand_red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        await channel.send(embed=embed)


    @app_commands.command(name="lock", description="Lock a channel")
    @app_commands.guild_only()
    @has_roles(admin=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(channel="The channel to lock", reason="The reason for locking the channel")
    async def lock(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel | None = None, reason: str = "No reason provided.") -> None:
        await interaction.response.defer(ephemeral=True)
        channel = channel if channel is not None else interaction.channel
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False, create_public_threads=False,
                                    create_private_threads=False, send_messages_in_threads=False,
                                    add_reactions=False,
                                    create_polls=False)
        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="Channel Locked", description=f"- {reason}",
                colour=discord.Colour.brand_red(),
                timestamp=discord.utils.utcnow()
            )
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Unable to Send",
                    description=f"- Unable to send a message in {interaction.channel.mention}",
                    color=discord.Color.brand_red()
                )
                return await interaction.followup.send(embed=embed)

        channel_embed = discord.Embed(
            title=f"✅ Successfully locked {interaction.channel.mention}",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)


    @app_commands.command(name="unlock", description="The reason for unlocking the channel")
    @app_commands.guild_only()
    @has_roles(admin=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(channel="The channel to unlock", reason="The reason for unlocking the channel")
    async def unlock(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel | None = None, reason: str = "No reason provided.") -> None:
        await interaction.response.defer(ephemeral=True)
        channel = channel if channel is not None else interaction.channel
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True, create_public_threads=True,
                                    create_private_threads=True, send_messages_in_threads=True,
                                    add_reactions=True,
                                    create_polls=True)
        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="Channel Unlocked", description=f"- {reason}",
                colour=discord.Colour.brand_green(),
                timestamp=discord.utils.utcnow()
            )
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Unable to Send",
                    description=f"- Unable to send a message in {interaction.channel.mention}",
                    color=discord.Color.brand_red()
                )
                return await interaction.followup.send(embed=embed)

        channel_embed = discord.Embed(
            title=f"✅ Successfully unlocked {interaction.channel.mention}",
            color=discord.Color.brand_green(),
        )
        await interaction.followup.send(embed=channel_embed)

    @app_commands.command(name="masskick", description="Kick multiple people")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(users="The list of users to kick | Use @user or user ID")
    @has_roles(admin=True, snr=True)
    async def masskick(self, interaction: discord.Interaction, users: str):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Masskick",
            description="Are you sure you want to execute this?",
            color=discord.Color.brand_red(),
        )
        members_list = set()
        for user in users.split():
            if 22 >= len(user) > 17:
                user_id = int(user.strip("<@>"))
                member = interaction.guild.get_member(user_id)
                if member is None:
                    continue
                members_list.add(member)
        view = MassView(members_list, "masskick", interaction.user.id, interaction)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


    @app_commands.command(name="massban", description="Ban multiple people")
    @app_commands.guild_only()
    @has_roles(admin=True, snr=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(users="The list of users to ban | Use @user or user ID")
    async def massban(
        self, interaction: discord.Interaction, users: str
    ):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Massban",
            description="Are you sure you want to execute this?\
                \n-# Do note that users will not receive the link to the appeal server!",
            color=discord.Color.brand_red(),
        )
        users_list = set()
        for user in users.split():
            user_id = user.strip("<@>")
            if not 22 >= len(user_id) > 16:
                continue
            user = interaction.guild.get_member(int(user_id))
            if user is not None:
                if user.top_role >= interaction.user.top_role:
                    continue
            users_list.add(int(user_id))
        if not users_list:
            embed = discord.Embed(
                title="An error occurred",
                description=f"You are unable to ban all the members given.",
                color=discord.Color.brand_red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        view = MassView(users_list, "massban", interaction.user.id, interaction)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


    @app_commands.command(name="massmute", description="Mute multiple people")
    @app_commands.guild_only()
    @has_roles(admin=True, snr=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(users="The list of users to mute | Use @user or user ID")
    async def massmute(self, interaction: discord.Interaction, users: str):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Massmute",
            description="Are you sure you want to execute this?",
            color=discord.Color.brand_red(),
        )
        members_list = set()
        for user in users.split():
            if 22 >= len(user) > 17:
                user_id = int(user.strip("<@>"))
                member = interaction.guild.get_member(user_id)
                if member is None:
                    continue
                members_list.add(member)
        view = MassView(members_list, "massmute", interaction.user.id, interaction)
        await interaction.followup.send(embed=embed, view=view)


    @app_commands.command(name="massunban", description="Unban multiple people")
    @app_commands.guild_only()
    @has_roles(admin=True, snr=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(users="The list of users to unban | Use user ID")
    async def massunban(self, interaction: discord.Interaction, users: str):
        embed = discord.Embed(
            title="Massunban",
            description="Are you sure you want to execute this?",
            color=discord.Color.brand_red(),
        )
        users_list = [int(user.strip("<@>")) if not user.isdigit() else int(user) for user in users.split() if 22 >= len(user) > 17]
        view = MassView(users_list, "massunban", interaction.user.id, interaction)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


    @app_commands.command(name="case", description="Get information about a case")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    @app_commands.describe(case_id = "The case ID of the case")
    @has_roles(admin=True, mod=True, appeal_staff=True)
    async def case(self, interaction: discord.Interaction, case_id: str):
        await interaction.response.defer()
        async with self.bot.mod_pool.acquire() as conn:
            row = await conn.execute(
                """SELECT user_id, action, mod_id, time, log_id FROM moddb WHERE case_id = ? """,
                (case_id,),
            )
            result = await row.fetchone()
        if result is None:
            embed = discord.Embed(
                title=f"❌ No such case: `{case_id}`", color=discord.Color.brand_red()
            )
            await interaction.followup.send(embed=embed)
        else:
            try:
                user = self.bot.get_user(
                    result["user_id"]
                ) or await self.bot.fetch_user(result["user_id"])
            except discord.NotFound as e:
                embed = discord.Embed(title="An error occurred",
                                      description=f"- {e}")
                return await interaction.followup.send(embed=embed)
            try:
                mod = self.bot.get_user(result["mod_id"]) or await self.bot.fetch_user(
                    result["mod_id"]
                )
            except discord.NotFound as e:
                return await interaction.followup.send(f"An error occurred: {e}")
            action : str = result["action"]
            timestamp : int = int(result["time"])
            log_id : int = result["log_id"]
            embed = discord.Embed(
                title=f"Case Info",
                description=f">>> **User:** {user.mention} ({user.id})\n**Action:** {action.title()}\
                                    \n**Created on:** <t:{timestamp}:f>",
                color=discord.Color.blurple(),
            )
            embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(
                text=f"Mod: @{mod} ({mod.id})", icon_url=mod.display_avatar.url
            )
            await interaction.followup.send(embed=embed, view=JumpToCase(log_id, self.bot.main_guild_id, self.bot.mod_log))


    @app_commands.command(name="cases", description="Get the last 30 cases")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    @has_roles(admin=True, mod=True, appeal_staff=True)
    async def cases(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute(
                """SELECT case_id, user_id, action, mod_id, time FROM moddb
                                      ORDER BY time DESC LIMIT 30"""
            )
            results = await rows.fetchall()
        if results:
            results_per_page = 15
            data = [
                f"- <@{result['user_id']}> **{result["action"].capitalize()}** by <@{result["mod_id"]}> (`{result["case_id"]}`) | <t:{int(result["time"])}:d>"
                for result in results
            ]
            embeds = [
                discord.Embed(
                    title="Last 30 cases",
                    description=f">>> {'\n'.join(data[i:i + results_per_page])}",
                )for i in range(0, len(results), results_per_page)]
            paginator = ButtonPaginator(embeds)
            await paginator.start(interaction)
        else:
            embed = discord.Embed(
                title=f"❌ No cases", color=discord.Color.brand_red()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="caselist-user", description="Get cases of a user")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(user = "The user to get cases of")
    @has_roles(admin=True, mod=True, appeal_staff=True)
    async def caselist_user(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute(
                """SELECT case_id, action, mod_id, time FROM moddb WHERE user_id = ?
                                      ORDER BY time DESC""",
                (user.id,),
            )
            results = await rows.fetchall()
        if results:
            results_per_page = 15
            data = [
                f"- **{result["action"].capitalize()}** by <@{result["mod_id"]}> (`{result["case_id"]}`) | <t:{int(result["time"])}:f>"
                for result in results
            ]
            embeds = [
                discord.Embed(
                    title="Case list",
                    description=f">>> {'\n'.join(data[i:i + results_per_page])}",
                ).set_author(
                    name=f"@{user} ({user.id})", icon_url=user.display_avatar.url
                )
                for i in range(0, len(results), results_per_page)
            ]
            paginator = ButtonPaginator(embeds)
            await paginator.start(interaction)
        else:
            embed = discord.Embed(
                title=f"❌ No cases found for @{user}", color=discord.Color.brand_red()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="caselist-mod", description="Get cases of a mod")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(mod = "The user to get cases of")
    @has_roles(admin=True, mod=True, appeal_staff=True)
    async def caselist_mod(self, interaction: discord.Interaction, mod: discord.User):
        await interaction.response.defer()
        async with self.bot.mod_pool.acquire() as conn:
            rows = await conn.execute(
                """SELECT case_id, user_id, action, time FROM moddb WHERE mod_id = ?
                                      ORDER BY time DESC""",
                (mod.id,),
            )
            results = await rows.fetchall()
        if results:
            results_per_page = 15
            data = [
                f"- **{result["action"].capitalize()}** <@{result["user_id"]}> (`{result["case_id"]}`) | <t:{int(result["time"])}:f>"
                for result in results
            ]
            embeds = [
                discord.Embed(
                    title="Case List",
                    description=f">>> {'\n'.join(data[i:i + results_per_page])}",
                ).set_footer(
                    text=f"Mod: @{mod} ({mod.id})", icon_url=mod.display_avatar.url
                )
                for i in range(0, len(results), results_per_page)
            ]
            paginator = ButtonPaginator(embeds)
            await paginator.start(interaction)
        else:
            embed = discord.Embed(
                title=f"❌ No cases found for moderator: @{mod}",
                color=discord.Color.brand_red(),
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="deletecase",  description="Delete a case")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(case_id = "The case ID of the case to delete")
    @has_roles(admin=True)
    async def deletecase(self, interaction: discord.Interaction, case_id: str) -> None:
        await interaction.response.defer(ephemeral=True)
        async with self.bot.mod_pool.acquire() as conn:
            row = await conn.execute(
                """SELECT NULL FROM moddb WHERE case_id = ?""", (case_id,)
            )
            result = await row.fetchone()
            if result:
                await conn.execute(
                    """DELETE FROM moddb WHERE case_id  =?""", (case_id,)
                )
        if result:
            embed = discord.Embed(
                title=f"✅ Successfully deleted case `{case_id}`",
                color=discord.Color.brand_green(),
            )
            log_embed = discord.Embed(
                title=f"Case deleted `{case_id}`",
                description=f"- Deleted by {interaction.user.mention} ({interaction.user.id})",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            log_embed.set_footer(
                text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url
            )
            channel = interaction.guild.get_channel(self.bot.mod_log)
            await channel.send(embed=log_embed)
        else:
            embed = discord.Embed(
                title=f"❌ There is no such case_id `{case_id}`",
                color=discord.Color.brand_red(),
            )
        await interaction.followup.send(embed=embed)


async def setup(bot: ModBot):
    await bot.add_cog(ModCog(bot))


class MassView(discord.ui.View):
    def __init__(
        self,
        users: list[discord.Object] | list[discord.User] | list[discord.Member],
        action: str,
        mod_id: int,
        old_interaction: discord.Interaction
    ):
        super().__init__(timeout=900)
        self.users = users
        self.action = action
        self.mod_id = mod_id
        self.old_interaction = old_interaction
    @discord.ui.button(
        label="Yes", style=discord.ButtonStyle.green, custom_id="MassPunish"
    )
    async def callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.action == "massban":
            await interaction.response.send_modal(MassBanModal(self.users))
        elif self.action == "massmute":
            await interaction.response.send_modal(MassMuteModal(self.users))
        elif self.action == "massunban":
            await interaction.response.send_modal(MassUnbanModal(self.users))
        elif self.action == "masskick":
            await interaction.response.send_modal(MassKickModal(self.users))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="CancelMassPunish")
    async def callback2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.old_interaction.delete_original_response()

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.mod_id


class MassBanModal(discord.ui.Modal):
    def __init__(self, users: list[discord.Object]):
        super().__init__(title="Massban", timeout=900, custom_id="Massban")
        self.actual_users = users
        self.users_split = ",".join(str(user_id) for user_id in users)
        self.users = discord.ui.Label(
            text="Users",
            description="To add more users, add their user id and separate them with commas (no spaces)",
            component=discord.ui.TextInput(
            default=self.users_split,
            required=True,
            min_length=18,
            max_length=1000,
            style=discord.TextStyle.long),
        )
        self.reason = discord.ui.Label(
            text="Reason",
            component= discord.ui.TextInput(
            placeholder = "The reason for the massban",
            default="No reason provided.",
            required=False,
            min_length=1,
            max_length=1000,
            style=discord.TextStyle.long,),
        )
        self.add_item(self.users)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction[ModBot]):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Now attempting to ban the users... This might take a while",
            ephemeral=True,
        )
        bot : ModBot = interaction.client

        users_submitted : str = self.users.component.value #type: ignore
        reason : str = self.reason.component.value #type: ignore

        if self.users_split != users_submitted:
            to_ban = []
            for user_id in users_submitted.split(","):
                try:
                    member = interaction.guild.get_member(
                        int(user_id)
                    ) or await interaction.guild.fetch_member(int(user_id))
                    if member and member.top_role >= interaction.user.top_role:
                        continue
                except discord.NotFound:
                    pass
                to_ban.append(discord.Object(user_id))
        else:
            to_ban = [
                discord.Object(user_id) for user_id in users_submitted.split(",")
            ]
        try:
            result = await interaction.guild.bulk_ban(
                to_ban, reason=f"Banned by {interaction.user} for: {reason}"
            )
            if result.banned:
                banned = []
                insert_value = []
                for user in result.banned:
                    case_id = convert_to_base64()
                    banned.append(f"{user.id} | `{case_id}`")
                    insert_value.append(
                        (case_id, user.id, "ban", interaction.user.id, time.time())
                    )

        except discord.HTTPException as e:
            return await interaction.followup.send(f"An error occurred: {e}")
        response_embed = discord.Embed(
            title=(
                f"{f"✅ Successfully massbanned {len(result.banned)}"}/{len(users_submitted.split(","))} users"
                if result.banned
                else f"❌ Failed to massban all users."
            ),
            color=(
                discord.Color.brand_green()
                if result.banned
                else discord.Color.brand_red()
            ),
        )
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        if interaction.message:
            await interaction.delete_original_response()

        if result.banned:
            channel = interaction.guild.get_channel(interaction.client.mod_log)
            embed = discord.Embed(
                title=f"Massbanned [{len(result.banned)}]",
                description=f">>> - {"\n- ".join(banned)}",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(
                name=f"Banned by",
                value=f">>> {interaction.user.mention} ({interaction.user.id})\
                    \n**Reason:** {reason}",
                inline=False,
            )
            embed.set_footer(
                text=f"@{interaction.user}",
                icon_url=interaction.user.display_avatar.url,
            )
            log_message = await channel.send(embed=embed)

            async with bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(
                        f"""INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)""",
                        [(*row, log_message.id) for row in insert_value],
                    )


class MassMuteModal(discord.ui.Modal):
    def __init__(self, users: list[discord.Member]):
        super().__init__(title="Massmute", timeout=900, custom_id="Massmute")
        self.actual_users = users
        self.users_split = ",".join(str(user.id) for user in users)
        self.users = discord.ui.Label(
            text="Users",
            description="To add more users, add their user id and separate them with commas (no spaces)",
            component = discord.ui.TextInput(
            default=self.users_split,
            required=True,
            min_length=18,
            max_length=1000,
            style=discord.TextStyle.long),
        )
        self.duration = discord.ui.Label(
            text="Duration",
            component = discord.ui.TextInput(
            placeholder="The length of the mute, e.g: 3h, 5d,10m",
            style=discord.TextStyle.short,
            required=True,
            max_length=20,
            min_length=2,),
        )
        self.reason = discord.ui.Label(
            text="Reason",
            component = discord.ui.TextInput(
            placeholder="The reason for the massban",
            default="No reason provided.",
            required=False,
            min_length=1,
            max_length=1000,
            style=discord.TextStyle.long,),
        )
        self.add_item(self.users)
        self.add_item(self.duration)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction[ModBot]):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Now attempting to mute the users... This might take a while",
            ephemeral=True,
        )

        duration_submitted : str = self.duration.component.value #type: ignore
        users_submitted : str = self.users.component.value #type: ignore
        reason : str = self.reason.component.value #type: ignore

        td = datetime.timedelta()
        duration_list = [duration for duration in duration_submitted.split(",")]
        for duration in duration_list:
            if duration.endswith("s"):
                new_time = duration.strip("s")
                td += datetime.timedelta(seconds=int(new_time))
            elif duration.endswith("m"):
                new_time = duration.strip("m")
                td += datetime.timedelta(minutes=int(new_time))
            elif duration.endswith("h"):
                new_time = duration.strip("h")
                td += datetime.timedelta(hours=int(new_time))
            elif duration.endswith("hour"):
                new_time = duration.strip("hour")
                td += datetime.timedelta(hours=int(new_time))
            elif duration.endswith("d"):
                new_time = duration.strip("d")
                td += datetime.timedelta(days=int(new_time))
            else:
                return await interaction.followup.send(
                    f"Invalid duration: `3h` or `10m,5d`", ephemeral=True
                )
        total_seconds = int(td.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if days > 28:
            return await interaction.followup.send(
                "The maximum mute time is 28 days. Please set a mute time below it.",
                ephemeral=True,
            )
        duration_message_parts = []
        if days > 0:
            duration_message_parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            duration_message_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            duration_message_parts.append(
                f"{minutes} minute{'s' if minutes > 1 else ''}"
            )
        if seconds > 0:
            duration_message_parts.append(
                f"{seconds} second{'s' if seconds != 1 else ''}"
            )

        duration_message = " and ".join(duration_message_parts)
        user_embed = discord.Embed(
            title="You have been muted",
            description=f">>> **Duration:** {duration_message}\n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_red(),
        )
        user_embed.set_author(
            name=interaction.guild.name, icon_url=interaction.guild.icon.url
        )
        muted = []
        insert_value = []
        bot : ModBot = interaction.client
        if [self.users_split] != users_submitted:
            for member_id in users_submitted.split(","):
                try:
                    member = interaction.guild.get_member(
                        int(member_id)
                    ) or await interaction.guild.fetch_member(int(member_id))
                except discord.NotFound:
                    continue
                if member.guild_permissions.administrator:
                    continue
                if member.top_role >= interaction.user.top_role:
                    continue
                try:
                    await member.timeout(
                        td,
                        reason=f"Muted by {interaction.user} for: {reason}",
                    )
                except Exception:
                    continue
                case_id = convert_to_base64()
                muted.append(f"{member.id} | `{case_id}`")
                insert_value.append(
                    (case_id, member.id, "mute", interaction.user.id, time.time())
                )
                if not member.bot:
                    try:
                        await member.send(embed=user_embed, view=AppealView())
                    except discord.Forbidden:
                        pass
        else:
            for user in self.actual_users:
                if user.top_role >= interaction.user.top_role:
                    continue
                if user.guild_permissions.administrator:
                    continue
                try:
                    await user.timeout(
                        td,
                        reason=f"Muted by {interaction.user} for: {reason}",
                    )
                except Exception:
                    continue
                case_id = convert_to_base64()
                muted.append(f"{user.id} | `{case_id}`")
                insert_value.append(
                    (case_id, user.id, "mute", interaction.user.id, time.time())
                )
                if not user.bot:
                    try:
                        await user.send(embed=user_embed, view=AppealView())
                    except discord.Forbidden:
                        pass
        response_embed = discord.Embed(
            title=(
                f"✅ Successfully massmuted {len(muted)}/{len(users_submitted.split(","))} users"
                if muted
                else f"❌ Failed to massmute all the users."
            ),
            color=discord.Color.brand_green() if muted else discord.Color.brand_red(),
        )
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        if interaction.message:
            await interaction.delete_original_response()

        if muted:
            channel = interaction.guild.get_channel(interaction.client.mod_log)
            embed = discord.Embed(
                title=f"Massmuted [{len(muted)}",
                description=f">>> - {"\n- ".join(muted)}",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(
                name=f"Muted by",
                value=f">>> {interaction.user.mention} ({interaction.user.id})\
                    \n**Duration:** {duration_message}\n**Reason:** {reason}",
                inline=False,
            )
            embed.set_footer(
                text=f"@{interaction.user}",
                icon_url=interaction.user.display_avatar.url,
            )
            log_message = await channel.send(embed=embed)

            async with bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(
                        f"""INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)""",
                        [(*row, log_message.id) for row in insert_value],
                    )


class MassUnbanModal(discord.ui.Modal):
    def __init__(self, users: list[discord.Object]):
        super().__init__(title="Massunban", timeout=900, custom_id="Massunban")
        users_split = ",".join(str(user_id) for user_id in users)
        self.users = discord.ui.Label(
            text="Users",
            description="To add more users, add their user id and separate them with commas (no spaces)",
            component = discord.ui.TextInput(
            default=users_split,
            required=True,
            min_length=18,
            max_length=1000,
            style=discord.TextStyle.long,),
        )
        self.reason = discord.ui.Label(
            text="Reason",
            component = discord.ui.TextInput(
            placeholder="The reason for the massunban",
            default="No reason provided.",
            required=False,
            min_length=1,
            max_length=1000,
            style=discord.TextStyle.long,),
        )
        self.add_item(self.users)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction[ModBot]):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Now attempting to unban the users... This might take a while",
            ephemeral=True,
        )
        users_submitted : str = self.users.component.value #type: ignore
        reason : str = self.reason.component.value #type: ignore
        unbanned = []
        insert_value = []
        to_unban = [
            user_id
            for user_id in users_submitted.split(",")
            if int(user_id) in [ban.user.id async for ban in interaction.guild.bans()]
        ]
        bot : ModBot = interaction.client
        for user_id in to_unban:
            try:
                await interaction.guild.unban(
                    discord.Object(int(user_id)),
                    reason=f"Unbanned by {interaction.user} for: {reason}",
                )
            except Exception:
                continue
            case_id = convert_to_base64()
            unbanned.append(f"{user_id} | `{case_id}`")
            insert_value.append(
                (case_id, int(user_id), "unban", interaction.user.id, time.time())
            )

        response_embed = discord.Embed(
            title=(
                f"{f"✅ Successfully unbanned {len(unbanned)}/{len(users_submitted.split(","))}"} users"
                if unbanned
                else f"❌ Failed to massunban all users."
            ),
            color=(
                discord.Color.brand_green() if unbanned else discord.Color.brand_red()
            ),
        )
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        if interaction.message:
            await interaction.delete_original_response()

        if unbanned:
            channel = interaction.guild.get_channel(interaction.client.mod_log)
            embed = discord.Embed(
                title=f"Massunbanned [{len(unbanned)}]",
                description=f">>> - {"\n- ".join(unbanned)}",
                color=discord.Color.brand_green(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(
                name=f"Unbanned by",
                value=f">>> {interaction.user.mention} ({interaction.user.id})\
                    \n**Reason:** {reason}",
                inline=False,
            )
            embed.set_footer(
                text=f"@{interaction.user}",
                icon_url=interaction.user.display_avatar.url,
            )
            log_message = await channel.send(embed=embed)

            async with bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(
                        f"""INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)""",
                        [(*row, log_message.id) for row in insert_value]
                    )


class MassKickModal(discord.ui.Modal):
    def __init__(self, users: set[discord.Member]):
        super().__init__(title="Masskick", timeout=900, custom_id="Masskick")
        self.actual_users = users
        self.users_split = ",".join(str(user.id) for user in users)
        self.users = discord.ui.Label(
            text="Users",
            description="To add more users, add their user id and separate them with commas (no spaces)",
            component = discord.ui.TextInput(
            default=self.users_split,
            required=True,
            min_length=18,
            max_length=1000,
            style=discord.TextStyle.long,),
        )
        self.reason = discord.ui.Label(
            text="Reason",
            component= discord.ui.TextInput(
            placeholder="The reason for the massban",
            default="No reason provided.",
            required=False,
            min_length=1,
            max_length=1000,
            style=discord.TextStyle.long,),
        )
        self.add_item(self.users)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction[ModBot]):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Now attempting to kick the users... This might take a while",
            ephemeral=True,
        )

        kicked = []
        insert_value = []
        users_submitted = self.users.component.value #type: ignore
        reason = self.reason.component.value #type: ignore
        bot : ModBot = interaction.client
        
        user_embed = discord.Embed(
            title="You have been kicked",
            description=f">>> **Reason:** {reason}",
            color=discord.Color.brand_red(),
            timestamp=discord.utils.utcnow(),
        )
        user_embed.set_author(
            name=interaction.guild.name, icon_url=interaction.guild.icon.url
        )
        user_embed.set_thumbnail(url=interaction.guild.icon.url)
        if self.users_split != users_submitted:
            for member_id in users_submitted.split(","):
                try:
                    member = interaction.guild.get_member(
                        member_id
                    ) or await interaction.guild.fetch_member(member_id)
                except discord.NotFound:
                    continue
                if member.top_role >= interaction.user.top_role:
                    continue
                if not member.bot:
                    try:
                        await member.send(embed=user_embed)
                    except discord.Forbidden:
                        pass
                try:
                    await interaction.guild.kick(
                        user,
                        reason=f"Kicked by {interaction.user} for: {reason}",
                    )
                except discord.Forbidden:
                    continue
                case_id = convert_to_base64()
                kicked.append(f"{member.id} | `{case_id}`")
                insert_value.append(
                    (case_id, member.id, "kick", interaction.user.id, time.time())
                )

        else:
            for user in self.actual_users:
                if user.top_role >= interaction.user.top_role:
                    continue
                if not user.bot:
                    user_embed = discord.Embed(
                        title="You have been kicked",
                        description=f">>> **Reason:** {reason}",
                        color=discord.Color.brand_red(),
                        timestamp=discord.utils.utcnow(),
                    )
                    user_embed.set_author(
                        name=interaction.guild.name, icon_url=interaction.guild.icon.url
                    )
                    user_embed.set_thumbnail(url=interaction.guild.icon.url)
                    try:
                        await user.send(embed=user_embed, view=AppealView())
                    except discord.Forbidden:
                        pass
                try:
                    await interaction.guild.kick(
                        user,
                        reason=f"Kicked by {interaction.user} for: {reason}",
                    )
                except Exception:
                    continue
                case_id = convert_to_base64()
                kicked.append(f"{user.id} | `{case_id}`")
                insert_value.append(
                    (case_id, user.id, "kick", interaction.user.id, time.time())
                )
        response_embed = discord.Embed(
            title=(
                f"✅ Successfully masskicked {len(kicked)}/{len(users_submitted.split(","))}!"
                if kicked
                else f"❌ Failed to masskick all users."
            ),
            color=discord.Color.brand_green() if kicked else discord.Color.brand_red(),
        )
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        if interaction.message:
            await interaction.delete_original_response()

        if kicked:
            channel = interaction.guild.get_channel(interaction.client.mod_log)
            embed = discord.Embed(
                title=f"Masskicked [{len(kicked)}]",
                description=f">>> - {"\n- ".join(kicked)}",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(
                name=f"Kicked by",
                value=f">>> {interaction.user.mention} ({interaction.user.id})\
                    \n**Reason:** {reason}",
                inline=False,
            )
            embed.set_footer(
                text=f"@{interaction.user}",
                icon_url=interaction.user.display_avatar.url,
            )
            log_message = await channel.send(embed=embed)

            async with bot.mod_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(
                        f"""INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)""",
                        [(*row, log_message.id) for row in insert_value]
                    )


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


class PreviousCase(discord.ui.View):
    def __init__(self, message_id: int, guild_id: int, mod_log: int):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Tempban Case",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{guild_id}/{mod_log}/{message_id}",
            )
        )

class JumpToCase(discord.ui.View):
    def __init__(self, log_id: int, guild_id: int, mod_log: int):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Jump to Case",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{guild_id}/{mod_log}/{log_id}",
            )
        )