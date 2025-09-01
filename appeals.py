from __future__ import annotations

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, Literal
from uuid import uuid4
import time
import base64
from functions import save_to_appealdb, delete_from_appealdb, save_to_moddb, double_query, convert_to_base64
from paginator import ButtonPaginator

if TYPE_CHECKING:
    from main import ModBot
    

MAIN_SERVER = 1319213192064536607
APPEAL_SERVER = 1342763981370298409

APPEAL_CHANNEL = 1353850807719694439
MOD_LOG = 1411982484744175638

APPEAL_STAFF_LEADER = 1344364861659943025
APPEAL_STAFF = 1353836099214119002
NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
MODERATOR = 1319214233803816960
SENIOR = 1343556008223707156
ADMIN = (
    1319213465390284860,
    1343556153657004074,
    1356640586123448501,
    1343579448020308008,
)
SACUL = 1294291057437048843


class AppealCog(commands.Cog):
    def __init__(self, bot: ModBot):
        self.bot = bot
        self.bot.add_view(AppealView())
        self.bot.add_view(AcceptDenyView())
    
    @commands.command(name="setup_appeal")
    @commands.has_any_role(APPEAL_STAFF_LEADER)
    @commands.guild_only()
    async def setup_appeal(self, ctx: commands.Context) -> None:
        await ctx.message.delete()
        if ctx.guild.id != APPEAL_SERVER:
            embed = discord.Embed(title="Wrong Server",
                                  description=f"- This command can only be used in the appeal server.",
                                  color=discord.Color.brand_red())
            return await ctx.send(embed=embed, delete_after=5.0)

        await ctx.send(view=AppealView())

    @setup_appeal.error
    async def setup_appeal_error(self, ctx: commands.Context, error):
        pass


async def setup(bot: ModBot):
    await bot.add_cog(AppealCog(bot))

class AppealModal(discord.ui.Modal):
    def __init__(self, action: Literal['mute', 'ban', 'warn']):
        super().__init__(title=f"Create {action.capitalize()} Appeal", timeout=15*60)
        self.action = action
        self.question = discord.ui.Label(text="What did you do?",
                                        component= discord.ui.TextInput(
                                        required=True, style=discord.TextStyle.long,
                                        placeholder="What caused you to be moderated?"))
        self.reason = discord.ui.Label(text="Why are you appealing?",
                                        component= discord.ui.TextInput(
                                        required=True,
                                        style=discord.TextStyle.long,
                                        placeholder="Were falsely moderated or are you ready to join the server again?"))
        self.add_item(self.question)
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        bot : ModBot = interaction.client
        question : str = self.question.component.value #type: ignore
        reason : str = self.reason.component.value #type: ignore
        thread = await interaction.channel.create_thread(name=f"Appeal for {interaction.user}", invitable=False, type=discord.ChannelType.private_thread)
        await interaction.response.send_message(f"A thread has been created for you: {thread.mention}", ephemeral=True)
        await thread.send(view=AcceptDenyView(interaction.user, self.action, question, reason))
        await save_to_appealdb(bot, thread.id, interaction.user.id, self.action)

class AppealBanButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Appeal", custom_id="start_ban_appeal")
    
    async def callback(self, interaction:discord.Interaction):
        await interaction.response.send_modal(AppealModal("ban"))


class AppealMuteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Appeal", custom_id="start_mute_appeal")
    
    async def callback(self, interaction:discord.Interaction):
        await interaction.response.send_modal(AppealModal("mute"))


class AppealWarnButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Appeal", custom_id="start_warn_appeal")
    
    async def callback(self, interaction:discord.Interaction):
        await interaction.response.send_modal(AppealModal("warn"))



class AppealContainer(discord.ui.Container):
    def __init__(self):
        super().__init__()
        appeal_header = discord.ui.TextDisplay("## Appeal")
        appeal_text = discord.ui.TextDisplay("Hello! Unfortunately you have been moderated for violating our rules. However, you may appeal it.")
        ban_appeal_section = discord.ui.Section("- **Ban**", accessory=AppealBanButton())
        mute_appeal_section = discord.ui.Section("- **Mute**", accessory=AppealMuteButton())
        warn_appeal_section = discord.ui.Section("- **Warn**", accessory=AppealWarnButton())

        self.add_item(appeal_header)
        self.add_item(discord.ui.Separator())
        self.add_item(appeal_text)
        self.add_item(warn_appeal_section)
        self.add_item(mute_appeal_section)
        self.add_item(ban_appeal_section)

  
class AppealView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(AppealContainer())

class AcceptBanModal(discord.ui.Modal):
    def __init__(self, owner: discord.Member | discord.User):
        super().__init__(title="Accept Appeal", timeout=15*60, custom_id="accept_ban_appeal_modal")
        self.owner = owner
        self.reason = discord.ui.Label(text="Reason for accepting",
                                            component = discord.ui.TextInput(
                                            required=True,
                                            style=discord.TextStyle.long,
                                            placeholder="Why did you accept this appeal?"),
                                            )
        self.private_comment = discord.ui.Label(text="Private Commment",
                                                component = discord.ui.TextInput(
                                                required=False,
                                                style=discord.TextStyle.long,
                                                placeholder="Additional comments for staff only"))
        self.add_item(self.reason)
        self.add_item(self.private_comment)
    async def on_submit(self, interaction: discord.Interaction):
        bot : ModBot = interaction.client
        await interaction.response.defer(ephemeral=True)
        reason : str = self.reason.component.value #type: ignore
        private_comment = self.private_comment.component.value #type: ignore
        main_server = bot.get_guild(MAIN_SERVER)
        try:
            await main_server.unban(self.owner, reason=f"Appeal accepted by {interaction.user}: {reason}")
        except discord.NotFound:
            embed = discord.Embed(title="User is not banned",
                                  description=f"{self.owner.mention} is not banned.",
                                  color=discord.Color.brand_red())
            return await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            return await interaction.followup.send(f"Unable to unban {self.owner.mention}", ephemeral=True)
        message_list= [f"{message.author}: {message.content}" async for message in interaction.channel.history(limit=125) if not message.author.bot][::-1]
        messages = "\n".join(message_list)
        if len(messages) > 4045:
            messages = messages[:4044]
        embed = discord.Embed(title="", description=f"**Thread Logs** ({interaction.channel.mention})\n>>> {messages}", color=discord.Color.brand_green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Opened by", value=f">>> {self.owner.mention} ({self.owner.id})", inline=False)
        embed.add_field(name=f"Closed by", value=f">>> **Mod:** {interaction.user.mention}  ({interaction.user.id})\
                        \n**Reason:** {reason}\n-# Comments:  {private_comment}", inline=False)
        embed.set_author(name=f"@{self.owner}'s Ban Appeal Accepted", icon_url=self.owner.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        log_channel = interaction.guild.get_channel(APPEAL_CHANNEL)
        await interaction.channel.edit(archived=True, locked=True)

        user_embed = discord.Embed(title="Ban Appeal Accepted", description=f"Appeal: {interaction.channel.mention}", color=discord.Color.brand_green(), timestamp=discord.utils.utcnow())
        user_embed.add_field(name="Reason", value=f">>> {reason}", inline=False)
        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)

        try:
            await self.owner.send(embed=user_embed)
        except discord.Forbidden:
            pass
        await log_channel.send(embed=embed)
        await interaction.followup.send(f"Success!", ephemeral=True)

        case_id = convert_to_base64()

        main_log_channel = main_server.get_channel(MOD_LOG)
        case_embed = discord.Embed(
            title=f"Unbanned (`{case_id}`)",
            description=f">>> **User:** {self.owner.mention} ({self.owner.id})\
                                \n**Reason (Appealed):** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_green(),
        )

        case_embed.add_field(
            name=f"Unbanned by", value=f">>> {interaction.user.mention} ({interaction.user.id})"
        )
        case_embed.set_author(name=f"@{self.owner}", icon_url=self.owner.display_avatar.url)
        case_embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        case_embed.set_thumbnail(url=self.owner.display_avatar.url)
        log_message = await main_log_channel.send(embed=case_embed)
        await double_query(bot, query_one ='''INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)''', 
                           value_one=(case_id, self.owner.id, "unban", interaction.user.id, time.time(), log_message.id),

                           query_two ='''DELETE FROM appealdb WHERE thread_id = ?''', 
                           value_two=(interaction.channel_id,))


class AcceptMuteModal(discord.ui.Modal):
    def __init__(self, owner: discord.Member | discord.User):
        super().__init__(title="Accept Appeal", timeout=15*60, custom_id="accept_mute_appeal_modal")
        self.owner = owner
        self.reason = discord.ui.Label(text="Reason for accepting",
                                            component = discord.ui.TextInput(
                                            required=True,
                                            style=discord.TextStyle.long,
                                            placeholder="Why did you accept this appeal?"))
        self.private_comment = discord.ui.Label(text="Private Commment",
                                                component = discord.ui.TextInput(
                                                required=False,
                                                style=discord.TextStyle.long,
                                                placeholder="Additional comments for staff only"))
        self.add_item(self.reason)
        self.add_item(self.private_comment)
    async def on_submit(self, interaction: discord.Interaction):
        bot : ModBot = interaction.client
        await interaction.response.defer(ephemeral=True)
        reason = self.reason.component.value #type: ignore
        private_comment = self.private_comment.component.value #type: ignore
        main_server = interaction.client.get_guild(MAIN_SERVER)
        try:
            member = main_server.get_member(self.owner.id) 
            if member is None:
                embed = discord.Embed(title="Member not Found",
                                      description=f"- {self.owner.mention} is not longer a member in the main server. They cannot be unmuted.",
                                      color=discord.Colour.brand_red())
                return await interaction.followup.send(embed=embed, ephemeral=True)
            await member.timeout(None, reason=f"Appeal accepted by {interaction.user}: {reason}")
        except discord.Forbidden:
            embed = discord.Embed(title="An error occurred",
                                    description=f"- Unable to unmute {self.owner.mention}",
                                    color=discord.Colour.brand_red())
            return await interaction.followup.send(embed=embed, ephemeral=True)
        message_list= [f"{message.author}: {message.content}" async for message in interaction.channel.history(limit=125) if not message.author.bot][::-1]
        messages = "\n".join(message_list)
        if len(messages) > 4045:
            messages = messages[:4044]
        embed = discord.Embed(title="", description=f"**Thread Logs** ({interaction.channel.mention})\n>>> {messages}", color=discord.Color.brand_green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Opened by", value=f">>> {self.owner.mention} ({self.owner.id})", inline=False)
        embed.add_field(name=f"Closed by", value=f">>> **Mod:** {interaction.user.mention}  ({interaction.user.id})\
                        \n**Reason:** {reason}\n-# Comments:  {private_comment}", inline=False)
        embed.set_author(name=f"@{self.owner}'s Mute Appeal Accepted", icon_url=self.owner.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        log_channel = interaction.guild.get_channel(APPEAL_CHANNEL)
        await interaction.channel.edit(archived=True, locked=True)

        user_embed = discord.Embed(title="Mute Appeal Accepted", description=f"Appeal: {interaction.channel.mention}", color=discord.Color.brand_green(), timestamp=discord.utils.utcnow())
        user_embed.add_field(name="Reason", value=f">>> {reason}", inline=False)
        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)

        try:
            await self.owner.send(embed=user_embed)
        except discord.Forbidden:
            pass
        await log_channel.send(embed=embed)

        case_id = convert_to_base64()

        main_log_channel = main_server.get_channel(MOD_LOG)
        case_embed = discord.Embed(
            title=f"Unmuted (`{case_id}`)",
            description=f">>> **User:** {member.mention} ({member.id})\
                                \n**Reason (Appealed):** {reason}",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.brand_green(),
        )

        case_embed.add_field(
            name=f"Unmuted by", value=f">>> {interaction.user.mention} ({interaction.user.id})"
        )
        case_embed.set_author(name=f"@{member}", icon_url=member.display_avatar.url)
        case_embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        case_embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.followup.send(f"Success!", ephemeral=True)

        log_message = await main_log_channel.send(embed=case_embed)
        await double_query(bot, query_one='''INSERT INTO moddb (case_id, user_id, action, mod_id, time, log_id) VALUES (?, ?, ?, ?, ?, ?)''', 
                           value_one=(case_id, self.owner.id, "unmute", interaction.user.id, time.time(), log_message.id),

                           query_two='''DELETE FROM appealdb WHERE thread_id = ?''', 
                           value_two=(interaction.channel_id, ))


class AcceptWarnModal(discord.ui.Modal):
    def __init__(self, owner: discord.Member | discord.User):
        super().__init__(title="Accept Appeal", timeout=15*60, custom_id="accept_warn_appeal_modal")
        self.owner = owner
        self.reason = discord.ui.Label(text="Reason for accepting",
                                        component = discord.ui.TextInput(
                                        required=True,
                                        style=discord.TextStyle.long,
                                        placeholder="Why did you accept this appeal?"))
        self.private_comment = discord.ui.Label(text="Private Commment",
                                                component = discord.ui.TextInput(
                                                required=False,
                                                style=discord.TextStyle.long,
                                                placeholder="Additional comments for staff only"))
        self.add_item(self.reason)
        self.add_item(self.private_comment)
    async def on_submit(self, interaction: discord.Interaction):
        bot : ModBot = interaction.client
        await interaction.response.defer(ephemeral=True)
        reason : str = self.reason.component.value #type: ignore
        private_comment : str = self.private_comment.component.value #type: ignore
        message_list= [f"{message.author}: {message.content}" async for message in interaction.channel.history(limit=125) if not message.author.bot][::-1]
        messages = "\n".join(message_list)
        if len(messages) > 4045:
            messages = messages[:4044]
        embed = discord.Embed(title="", description=f"**Thread Logs** ({interaction.channel.mention})\n>>> {messages}", color=discord.Color.brand_green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Opened by", value=f">>> {self.owner.mention} ({self.owner.id})", inline=False)
        embed.add_field(name=f"Closed by", value=f">>> **Mod:** {interaction.user.mention}  ({interaction.user.id})\
                        \n**Reason:** {reason}\n-# Comments:  {private_comment}", inline=False)
        embed.set_author(name=f"@{self.owner}'s Appeal Accepted", icon_url=self.owner.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        log_channel = interaction.guild.get_channel(APPEAL_CHANNEL)
        await interaction.channel.edit(archived=True, locked=True)

        user_embed = discord.Embed(title="Appeal Accepted", description=f"Appeal: {interaction.channel.mention}", color=discord.Color.brand_green(), timestamp=discord.utils.utcnow())
        user_embed.add_field(name="Reason", value=f">>> {reason}", inline=False)
        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)

        try:
            await self.owner.send(embed=user_embed)
        except discord.Forbidden:
            pass
        await log_channel.send(embed=embed)
        await interaction.followup.send(f"Success!", ephemeral=True)

        await delete_from_appealdb(bot, interaction.channel_id)

class AcceptButton(discord.ui.Button):
    def __init__(self, owner: discord.Member | discord.User, action: Literal['ban', 'mute', 'warn']):
        super().__init__(style=discord.ButtonStyle.green, label="Accept", custom_id="accept_ban_appeal")
        self.owner = owner
        self.action = action

    async def callback(self, interaction):
        bot : ModBot = interaction.client
        owner = self.owner
        if owner is None:
            async with bot.mod_pool.acquire() as conn:
                row = await conn.execute('''SELECT user_id, action FROM appealdb WHERE thread_id = ?''',
                                   (interaction.channel.id, ))
                result = await row.fetchone()
                owner_id = result['user_id']
                action = result['action']
                
            owner = interaction.guild.get_member(owner_id)
            if owner is None:
                embed = discord.Embed(title="Member not Found",
                                      description=f"- `{owner_id}` is no longer in this server. Please close this thread manually.",
                                      color=discord.Color.brand_red())
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        if self.action is not None:
            if self.action == 'ban':
                await interaction.response.send_modal(AcceptBanModal(owner))
            elif self.action == 'mute':
                await interaction.response.send_modal(AcceptMuteModal(owner))
            else:
                await interaction.response.send_modal(AcceptWarnModal(owner))
        else:
            if action == 'ban':
                await interaction.response.send_modal(AcceptBanModal(owner))
            elif action == 'mute':
                await interaction.response.send_modal(AcceptMuteModal(owner))
            else:
                await interaction.response.send_modal(AcceptWarnModal(owner))


class DenyModal(discord.ui.Modal):
    def __init__(self, owner: discord.Member | discord.User):
        super().__init__(title="Deny Appeal", timeout=None, custom_id="deny_appeal_modal")
        self.owner = owner
        self.reason = discord.ui.Label(text="Reason for denying",
                                        component = discord.ui.TextInput(
                                        required=True,
                                        style=discord.TextStyle.long,
                                        placeholder="Why did you deny this appeal?"))
        self.private_comment = discord.ui.Label(text="Private Commment",
                                                component = discord.ui.TextInput(
                                                required=False,
                                                style=discord.TextStyle.long,
                                                placeholder="Additional comments for staff only"))
        self.add_item(self.reason)
        self.add_item(self.private_comment)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        bot : ModBot = interaction.client
        reason = self.reason.component.value #type: ignore
        private_comment = self.reason.component.value #type: ignore
        message_list= [f"{message.author}: {message.content}" async for message in interaction.channel.history(limit=125) if not message.author.bot][::-1]
        messages = "\n".join(message_list)
        if len(messages) > 4045:
            messages = messages[:4044]
        embed = discord.Embed(title="", description=f"**Thread Logs** ({interaction.channel.mention})\n>>> {messages}", color=discord.Color.brand_red(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Opened by", value=f">>> {self.owner.mention} ({self.owner.id})", inline=False)
        embed.add_field(name=f"Denied by", value=f">>> **Mod:** {interaction.user.mention}  ({interaction.user.id})\
                        \n**Reason:** {reason}\n-# Comments:  {private_comment}", inline=False)
        embed.set_author(name=f"@{self.owner}'s Appeal Denied", icon_url=self.owner.display_avatar.url)
        embed.set_footer(text=f"@{interaction.user}", icon_url=interaction.user.display_avatar.url)
        log_channel = interaction.guild.get_channel(APPEAL_CHANNEL)
        await interaction.channel.edit(archived=True, locked=True)

        user_embed = discord.Embed(title="Appeal Denied", description=f"Appeal: {interaction.channel.mention}", color=discord.Color.brand_red(), timestamp=discord.utils.utcnow())
        user_embed.add_field(name="Reason", value=f">>> {reason}", inline=False)
        user_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        user_embed.set_thumbnail(url=interaction.guild.icon.url)

        try:
            await self.owner.send(embed=user_embed)
        except discord.Forbidden:
            pass
        await log_channel.send(embed=embed)
        await interaction.followup.send(f"Success!", ephemeral=True)

        await delete_from_appealdb(bot, interaction.channel_id)

        
class DenyButton(discord.ui.Button):
    def __init__(self, owner: discord.Member | discord.User):
        super().__init__(style=discord.ButtonStyle.red, label="Deny", custom_id="deny_appeal")
        self.owner = owner
    async def callback(self, interaction: discord.Interaction):
        bot : ModBot = interaction.client
        owner = self.owner
        if owner is None:
            async with bot.mod_pool.acquire() as conn:
                row = await conn.execute('''SELECT user_id FROM appealdb WHERE thread_id = ?''',
                                   (interaction.channel_id, ))
                result = await row.fetchone()
                owner_id = result['user_id']
            owner = interaction.guild.get_member(owner_id)
            if owner is None: 
                embed = discord.Embed(title="Member not Found",
                                      description=f"- `{owner_id}` is no longer in the server. Please close this thread manually.",
                                      color=discord.Color.brand_red())
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(DenyModal(owner))

class CasesButton(discord.ui.Button):
    def __init__(self, owner: discord.Member | discord.User):
        super().__init__(style=discord.ButtonStyle.gray, label="view", custom_id="view_cases")
        self.owner = owner

    async def callback(self, interaction):
        bot : ModBot = interaction.client
        owner = self.owner
        if owner is None:
            async with bot.mod_pool.acquire() as conn:
                row = await conn.execute('''SELECT user_id FROM appealdb WHERE thread_id = ?''',
                                   (interaction.channel_id, ))
                result = await row.fetchone()
                owner_id = result['user_id']
            owner = interaction.guild.get_member(owner_id)
            if owner is None: 
                embed = discord.Embed(title="Member not Found",
                                      description=f"- `{owner_id}` is no longer in the server. Please close this thread manually.",
                                      color=discord.Color.brand_red())
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            rows = await conn.execute(
                """SELECT case_id, action, mod_id, time FROM moddb WHERE user_id = ?
                                      ORDER BY time DESC""",
                (owner.id),
            )
            results = await rows.fetchall()
        else:
            async with bot.mod_pool.acquire() as conn:
                rows = await conn.execute(
                    """SELECT case_id, action, mod_id, time FROM moddb WHERE user_id = ?
                                        ORDER BY time DESC""",
                    (owner.id),
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
                    name=f"@{owner} ({owner.id})", icon_url=owner.display_avatar.url
                )
                for i in range(0, len(results), results_per_page)
            ]
            paginator = ButtonPaginator(embeds)
            await paginator.start(interaction, ephemeral=True)
        else:
            embed = discord.Embed(
                title=f"❌ No cases found for @{owner}", color=discord.Color.brand_red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class AcceptDenyContainer(discord.ui.Container):
    def __init__(self, owner: discord.Member | discord.User, *, action: Literal['ban', 'warn', 'mute'], question: str, reason: str):
        super().__init__()
        appeal_type = discord.ui.TextDisplay(f"### {action.capitalize() if action else ""} Appeal")
        
        inform_text = discord.ui.TextDisplay(
            f"Hello {owner.mention if owner is not None else "there"}, the <@&1353836099214119002> have been informed. Please avoid pinging unnecessarily. If you have any further information, please send them below.")
        action_answer = discord.ui.TextDisplay(f"**What did you do?**\n>>> {question}")
        reason_answer = discord.ui.TextDisplay(f"**Why are you appealing?**\n>>> {reason}")
        cases_section = discord.ui.Section("Cases", accessory=CasesButton(owner))
        accept_section = discord.ui.Section("To accept", accessory=AcceptButton(owner, action=action))
        deny_section = discord.ui.Section("To deny", accessory=DenyButton(owner))
        self.add_item(appeal_type)
        self.add_item(inform_text)
        self.add_item(discord.ui.Separator())
        self.add_item(action_answer)
        self.add_item(reason_answer)
        self.add_item(discord.ui.Separator())
        self.add_item(cases_section)
        self.add_item(accept_section)
        self.add_item(deny_section)

class AcceptDenyView(discord.ui.LayoutView):
    def __init__(self, owner: discord.Member | discord.User | None = None, action: Literal['ban', 'warn', 'mute'] = None, question: str = None, reason: str = None):
        super().__init__(timeout=None)
        self.add_item(AcceptDenyContainer(owner, action=action, reason=reason, question=question))
    
    async def interaction_check(self, interaction: discord.Interaction):
        
        return any(role.id == APPEAL_STAFF for role in interaction.user.roles)
