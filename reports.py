from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
import datetime
from typing import TYPE_CHECKING
import re
from json import loads

from functions import get_field_content, get_user_id_from_avatar
from discord.utils import MISSING
from paginator import ButtonPaginator
if TYPE_CHECKING:
    from main import ModBot
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Build full path to the file
CONFIG_PATH = BASE_DIR / "config.json"
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        data = f.read()
        return loads(data)


data = load_config()
roles_data = data['roles']
channel_guild_data = data['channel_guild']

GUILD_ID = channel_guild_data['GUILD_ID']
MOD_LOG = channel_guild_data['MOD_LOG']
SACUL = roles_data['SACUL']
REPORT_CHANNEL = channel_guild_data['REPORT_CHANNEL']


class ReportCog(commands.Cog):
    def __init__(self, bot: ModBot) -> None:
        self.bot = bot
    
    @app_commands.command(name="report", description="Report a member or message")
    @app_commands.guild_only()
    @app_commands.choices(reason=[
            app_commands.Choice(name="Breaking ToS", value="Breaking Tos"),
            app_commands.Choice(name="Being Disrespectful and/or unwelcoming", value="Being Disrespectful and/or unwelcoming"),
            app_commands.Choice(name="Instigating/Participating in drama", value="Instigating/Participating in drama"),
            app_commands.Choice(name="NSFW", value="NSFW"),
            app_commands.Choice(name="Advertising", value="Advertising"),
            app_commands.Choice(name="Malicious Links", value="Malicious Links"),
            app_commands.Choice(name="Offtopic/Posting unrelevant content", value="Offtopic/Posting unrelevant content"),
            app_commands.Choice(name="Not respecting privacy", value="Not respecting privacy"),
            app_commands.Choice(name="Baiting or Spamming", value="Baiting or Spamming"),
            app_commands.Choice(name="Minimodding", value="Minimodding"),
        ])
    @app_commands.describe(user_or_message = "Enter a user with @ or enter a message link", reason = "The reason for reporting",
                           comments = "Any additional comments that you would like us to know")
    async def report(self, interaction: discord.Interaction, user_or_message: str, reason: str, comments: str | None = None):
        await interaction.response.defer(ephemeral=True)
        if user_or_message.isdigit() or user_or_message.startswith("<@") and user_or_message.endswith(">"):
            memberd_id = user_or_message.strip("<@>")
            member = interaction.guild.get_member(int(memberd_id))
            if member is None:
                embed = discord.Embed(title="Member Not Found",
                                      description=f"- There is no such member `{memberd_id}`. Try mentioning a user using `@` or enter a message link.",
                                      color=discord.Color.brand_red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            report_embed = discord.Embed(title="Member Report",
                                         description=f">>> **User:** {member.mention} ({member.id})\
                                            \n**Created on:** {discord.utils.format_dt(member.created_at, 'f')}\
                                            \n**Joined:** {discord.utils.format_dt(member.joined_at, 'f')}",
                                            color=discord.Color.orange(),
                                            timestamp=discord.utils.utcnow())
            report_embed.add_field(name="Reason", value=f">>> {reason}")
            if comments:
                report_embed.add_field(name="Comments",
                                    value=f">>> {comments}", inline = True)
            report_embed.add_field(name="Reported By",
                                   value=f">>> {interaction.user.mention} ({interaction.user.id})",
                                   inline=False)    
            report_embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
            report_embed.set_thumbnail(url=member.display_avatar.url)
            report_embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)

            report_channel : discord.TextChannel = self.bot.get_channel(REPORT_CHANNEL)
            await report_channel.send(embed=report_embed, view=AcceptDenyView())

            success_embed = discord.Embed(title="Success",
                                          description=f"- {member.mention} has been reported to the moderators",
                                          color=discord.Color.brand_green())
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            user_embed = discord.Embed(title="Your Report",
                                       description=f">>> **User:** {member.mention} ({member.id})\
                                        \n**Reason:** {reason}\
                                        \n**Comments:** {comments if comments else "None"}",
                                        color=discord.Color.blurple())
            user_embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
            user_embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await interaction.user.send(embed=user_embed)
            except discord.Forbidden:
                pass

        elif user_or_message.count("/") == 6:
            try:
                user_or_message_split = user_or_message.split('/')
                channel_id = user_or_message_split[5]
                message_id = user_or_message_split[6]
            except IndexError:
                embed = discord.Embed(title="Invalid Message Link",
                                      description=f"- {user_or_message} is not a valid message link.",
                                      color=discord.Color.brand_red())
                await interaction.followup.send()
                return
            channel = self.bot.get_partial_messageable(int(channel_id), guild_id=interaction.guild_id)
            try:
                message = await channel.fetch_message(int(message_id))
            except discord.NotFound:
                embed = discord.Embed(title="Message Not Found",
                                      description=f"- There is no such message `{message_id}`",
                                      color=discord.Color.brand_red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            report_embed = discord.Embed(title="Member Report",
                                         description=f">>> **User:** {message.author.mention} ({message.author.id})\
                                            \n**Created on:** {discord.utils.format_dt(message.author.created_at, 'f')}\
                                            \n**Joined:** {discord.utils.format_dt(message.author.joined_at, 'f')}",
                                            color=discord.Color.orange(),
                                            timestamp=discord.utils.utcnow())
            report_embed.add_field(name="Reason", value=f">>> {reason}")
            if comments:
                report_embed.add_field(name="Comments",
                                        value=f">>> {comments}", inline = True)
            report_embed.add_field(name="Message Reported",
                                   value=f">>> {message.content[0:900]} ({message.jump_url})", inline=False)
            report_embed.add_field(name="Reported By",
                                   value=f">>> {interaction.user.mention} ({interaction.user.id})",
                                   inline=False)
            report_embed.set_author(name=f"@{message.author}", icon_url=message.author.display_avatar.url)
            report_embed.set_thumbnail(url=message.author.display_avatar.url)
            report_embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)

            report_channel : discord.TextChannel = self.bot.get_channel(REPORT_CHANNEL)
            await report_channel.send(embed=report_embed, view=AcceptDenyView())
    
            success_embed = discord.Embed(title="Success",
                                          description=f"- {message.author.mention} has been reported to the moderators",
                                          color=discord.Color.brand_green())
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            user_embed = discord.Embed(title="Your Report",
                                       description=f">>> **User:** {message.author.mention} ({message.author.id})\
                                        \n**Reason:** {reason}\
                                        \n**Comments:** {comments if comments else "None"}\
                                        \n**Message Reported:** {message.jump_url}",
                                        color=discord.Color.blurple())
            user_embed.set_author(name=f"@{message.author}", icon_url=message.author.display_avatar.url)
            user_embed.set_thumbnail(url=message.author.display_avatar.url)
            try:
                await interaction.user.send(embed=user_embed)
            except discord.Forbidden:
                pass
        else:
            embed = discord.Embed(title="Invalid Input",
                                  description=f"- `{user_or_message}` is not a user or message link.\
                                    \nTry mentioning a user using `@` or enter a message link.")

async def setup(bot: ModBot) -> None:
    await bot.add_cog(ReportCog(bot))


class AcceptDenyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept_report")
    async def accept_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        embed = interaction.message.embeds[0] # type: ignore
        user_id1 = get_user_id_from_avatar(embed.author.icon_url)
        user_id2 = get_user_id_from_avatar(embed.thumbnail.url)
        
        if user_id1 is None and user_id2 is not None or user_id1 != user_id2:
            error_embed = discord.Embed(title="An Error Occurred",
                                        description=f"Unable to find the user ID from `{embed.author.icon_url}` and `{embed.thumbnail.url}`\
                                            \n- user_id1: {user_id1}\n- user_id2: {user_id2}\
                                            \n**Please notify <@{SACUL}>**")
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        user_id = user_id1
        try:
            user = interaction.client.get_user(user_id) or await interaction.client.fetch_user(user_id)
        except discord.NotFound:
            embed = discord.Embed(title="User Not Found",
                                  description=f"- No such user `{user_id}`",
                                  color=discord.Color.brand_red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        reported_by_id_str = get_user_id_from_avatar(embed.footer.icon_url)
        if reported_by_id_str is None:
            reported_by_text = get_field_content(embed, "Reported By")
            user_id = reported_by_text[reported_by_text.find('('): reported_by_text.rfind(')')]
            if user_id and user_id.isdigit():
                reported_by_id_str = user_id
            else:
                error_embed = discord.Embed(title="Unable to find User ID",
                                            description=f"- Unable to find user_id of the pesron who reported: `{user_id}`")
                await interaction.followup.send(embed=error_embed)
                return
        reported_by_id = int(reported_by_id_str)
        try:
            reported_by = interaction.guild.get_member(reported_by_id) or await interaction.client.fetch_user(reported_by_id)
        except discord.NotFound:
            embed = discord.Embed(title="User Not Found",
                                  description=f"- Unable to find the user `{reported_by_id}`",
                                  color=discord.Color.brand_red())
            await interaction.followup.send(embed=embed)
            return

        reason = get_field_content(embed, "Reason")
        comments = get_field_content(embed, "Comments")
        reported_message = get_field_content(embed, "Message Reported")

        user_embed = discord.Embed(title="Report Accepted",
                                   description=f"- Your report from {discord.utils.format_dt(interaction.message.created_at, 'R')} has been accepted",
                                   color=discord.Color.brand_green(),
                                   timestamp=discord.utils.utcnow())
        user_embed.add_field(name="Your Report",
                             value=f">>> **User:** {user.mention}\
                                \n**Reason:** {reason.removeprefix('>>> ')}\
                                \n**Comments:** {comments.removeprefix('>>> ') if comments else "None"}")
        if isinstance(reported_by, discord.Member) and not reported_by.bot:
            try:
                await reported_by.send(embed=user_embed)
            except discord.Forbidden:
                pass
        log_channel = interaction.guild.get_channel(MOD_LOG)
        log_embed = discord.Embed(title="Report Accepted",
                                  description=f">>> **User:** {user.mention} ({user.id})\
                                    \n**Created on:** {discord.utils.format_dt(user.created_at, 'f')}\
                                    \n**Joined:** {discord.utils.format_dt(user.joined_at, 'f') if isinstance(user, discord.Member) else "Unknown"}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_green())
        log_embed.add_field(name="Reason",
                            value=reason)
        if comments is not None:
            log_embed.add_field(name="Comments",
                                value=comments, inline=True)
        if reported_message is not None:
            log_embed.add_field(name="Reported Message",
                                value=reported_message, inline=False)
        log_embed.add_field(name="Reported By",
                            value=f">>> {reported_by.mention} ({reported_by.id})",
                            inline=False)
        log_embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        log_embed.set_thumbnail(url=user.display_avatar.url)
        log_embed.set_footer(text=f"@{interaction.user} ({interaction.user.id}) accepted this reported",
                            icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_embed)
        await interaction.followup.send(f"Success!", ephemeral=True)
        await interaction.message.delete()


    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="deny_buttn")
    async def deny_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DenyModal(interaction.message.embeds))

    @discord.ui.button(label="Cases", style=discord.ButtonStyle.gray, custom_id="view_cases")
    async def cases_callback(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        bot : ModBot = interaction.client
        embed = interaction.message.embeds[0]
        user_id1 = get_user_id_from_avatar(embed.author.icon_url)
        user_id2 = get_user_id_from_avatar(embed.thumbnail.url)
        
        if user_id1 is None and user_id2 is not None or user_id1 != user_id2:
            error_embed = discord.Embed(title="An Error Occurred",
                                        description=f"Unable to find the user ID from `{embed.author.icon_url}` and `{embed.thumbnail.url}`\
                                            \n- user_id1: {user_id1}\n- user_id2: {user_id2}\
                                            \n**Please notify <@{SACUL}>**")
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        user_id = user_id1
        try:
            user = bot.get_user(user_id) or await interaction.client.get_user(user_id)
        except discord.NotFound:
            embed = discord.Embed(title="User Not Found",
                                  description=f"- No such user `{user_id}`",
                                  color=discord.Color.brand_red())
            return await interaction.followup.send(embed=embed, ephemeral=True)


        async with bot.mod_pool.acquire() as conn:
            rows = await conn.execute(
                """SELECT case_id, action, mod_id, time FROM moddb WHERE user_id = ?
                                    ORDER BY time DESC""", (user_id, ))
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
                    name=f"@{user_id} ({user_id})", icon_url=user.display_avatar.url
                )
                for i in range(0, len(results), results_per_page)
            ]
            paginator = ButtonPaginator(embeds)
            await paginator.start(interaction, ephemeral=True)
        else:
            embed = discord.Embed(
                title=f"❌ No cases found for @{user}", color=discord.Color.brand_red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class DenyModal(discord.ui.Modal):
    def __init__(self, embeds: list[discord.Embed]) -> None:
        super().__init__(title="Deny Reason", timeout=None, custom_id="deny_modal")
        self.deny_reason = discord.ui.Label(text="Reason", description="Reason for denying", component=discord.ui.TextInput(style=discord.TextStyle.long, max_length=800,
                                                                                                                           required=True))
        self.add_item(self.deny_reason)
        self.embeds : list[discord.Embed] = embeds
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        deny_reason : str = self.deny_reason.component.value # type: ignore
        embed : discord.Embed = self.embeds[0] # type: ignore
        user_id1 = get_user_id_from_avatar(embed.author.icon_url)
        user_id2 = get_user_id_from_avatar(embed.thumbnail.url)
        
        if user_id1 is None and user_id2 is not None or user_id1 != user_id2:
            error_embed = discord.Embed(title="An Error Occurred",
                                        description=f"Unable to find the user ID from `{embed.author.icon_url}` and `{embed.thumbnail.url}`\
                                            \n- user_id1: {user_id1}\n- user_id2: {user_id2}\
                                            \n**Please notify <@{SACUL}>**")
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        user_id = user_id1
        try:
            user = interaction.guild.get_member(user_id) or await interaction.client.fetch_user(user_id)
        except discord.NotFound:
            embed = discord.Embed(title="User Not Found",
                                  description=f"- No such user `{user_id}`",
                                  color=discord.Color.brand_red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        reported_by_id_str = get_user_id_from_avatar(embed.footer.icon_url)
        if reported_by_id_str is None:
            reported_by_text = get_field_content(embed, "Reported By")
            if reported_by_text is None:
                await interaction.followup.send(f"Unabled to find reported by user, currently have: `{reported_by_text}`", ephemeral=True)
                return
            user_id = reported_by_text[reported_by_text.find('('): reported_by_text.rfind(')')]
            if user_id and user_id.isdigit():
                reported_by_id_str = user_id
            else:
                error_embed = discord.Embed(title="Unable to find User ID",
                                            description=f"- Unable to find user_id of the pesron who reported: `{user_id}`")
                await interaction.followup.send(embed=error_embed)
                return
        reported_by_id = int(reported_by_id_str)
        try:
            reported_by = interaction.guild.get_member(reported_by_id) or await interaction.client.fetch_user(reported_by_id)
        except discord.NotFound:
            embed = discord.Embed(title="User Not Found",
                                  description=f"- Unable to find the user `{reported_by_id}`",
                                  color=discord.Color.brand_red())
            await interaction.followup.send(embed=embed)
            return

        reason = get_field_content(embed, "Reason")
        comments = get_field_content(embed, "Comments")
        reported_message = get_field_content(embed, "Message Reported")

        user_embed = discord.Embed(title="Report Denied",
                                   description=f"- Your report from {discord.utils.format_dt(interaction.message.created_at, 'R')} has been denied.\
                                    \n  - {deny_reason}",
                                   color=discord.Color.brand_red(),
                                   timestamp=discord.utils.utcnow())
        user_embed.add_field(name="Your Report",
                             value=f">>> **User:** {user.mention}\
                                \n**Reason:** {reason.removeprefix('>>> ')}\
                                \n**Comments:** {comments.removeprefix('>>> ') if comments else "None"}")
        if isinstance(reported_by, discord.Member) and not reported_by.bot:
            try:
                await reported_by.send(embed=user_embed)
            except discord.Forbidden as e:
                pass
    
        log_channel = interaction.guild.get_channel(MOD_LOG)
        log_embed = discord.Embed(title="Report Denied",
                                 description=f">>> **User: **{user.mention} ({user.id})\
                                    \n**Created on:** {discord.utils.format_dt(user.created_at, 'f')}\
                                    \n**Joined:** {discord.utils.format_dt(user.joined_at, 'f') if isinstance(user, discord.Member) else "Unknown"}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
        log_embed.add_field(name="Reason",
                            value=reason)
        if comments is not None:
            log_embed.add_field(name="Comments",
                                value=comments, inline=True)
        if reported_message is not None:
            log_embed.add_field(name="Reported Message",
                                value=reported_message, inline=False)
        log_embed.add_field(name="Reported By",
                            value=f">>> {reported_by.mention} ({reported_by.id})", inline=False)
        log_embed.set_author(name=f"@{user}", icon_url=user.display_avatar.url)
        log_embed.set_thumbnail(url=user.display_avatar.url)
        log_embed.set_footer(text=f"@{interaction.user} ({interaction.user.id}) denied this report: {deny_reason}",
                             icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_embed)
        await interaction.followup.send("Success!", ephemeral=True)
        await interaction.message.delete()

