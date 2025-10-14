from __future__ import annotations

import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import time
from discord import app_commands
from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from main import ModBot



class Utilities(commands.Cog):
    def __init__(self, bot: ModBot):
        self.bot = bot
        self.embed = discord.Embed(
            title="❕Advertising Rules",
            description=f"You must have the <@&1330927524816883783>, <@&1319214818527412337> or <@&1338543708659777599> role to advertise.\
                                    \nSee <#1379844841793654784> for more information.",
            color=discord.Color.brand_red(),
        )
        self.embed.add_field(
            name="Rules:",
            value=f">>> - No off-topic messages\n- Maximum of 10 lines\n- Invite-for-reward servers are not allowed\
                                \n- Must comply with Discord ToS, Guidelines, and Ad Policy\n- Only 1 server per ad with a valid invite\
                                \n-  Asking others to check your ad or advertising elsewhere will result in a ban",
        )
        self.only_media = (f"Please note that you can only send links/images/videos in these channels!")
        self.last_sent_data : dict[int, discord.Message] = {}
        self.already_added = []

    @staticmethod
    def has_roles(admin: bool = False, mod: bool = False, snr: bool = False, appeal_staff: bool = False):
        async def predicate(ctx: commands.Context[ModBot]) -> bool:
            roles = [1294291057437048843]
            if admin:
                roles.extend(ctx.bot.admin)
            if mod:
                roles.extend(ctx.bot.mod)
            if snr:
                roles.extend(ctx.bot.senior)
            if appeal_staff:
                roles.extend(ctx.bot.appeal_staff)
            return any(role_id in ctx.author._roles for role_id in roles)
        return commands.check(predicate)

    async def cog_load(self):
        for channel_id in self.bot.sticky_channels:
            channel: discord.TextChannel = await self.bot.fetch_channel(channel_id)
            try:
                last_message_id = channel.last_message_id or 0
                last_message = await channel.fetch_message(last_message_id)
                if last_message.author == self.bot.user:
                    self.last_sent_data[channel_id] = last_message
                    continue
            except discord.NotFound:
                pass
            if channel.id == self.bot.sticky_channel:
                last_sent_message = await channel.send(embed=self.embed)
            else:
                last_sent_message = await channel.send(self.only_media)
            self.last_sent_data[channel_id] = last_sent_message
            await asyncio.sleep(0.25)


    @commands.Cog.listener("on_message")
    async def sticky_message_listener(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id == self.bot.sticky_channel:
            last_send_message: discord.Message | None = self.last_sent_data.get(message.channel.id)
            if last_send_message:
                if message.id != last_send_message.id:
                    try:
                        await last_send_message.delete()
                    except discord.NotFound:
                        return
                    new_last_sent = await message.channel.send(embed=self.embed)
                    self.last_sent_data[message.channel.id] = new_last_sent
        elif message.channel.id in self.bot.sticky_channels and message.channel.id != self.bot.sticky_channel:
            last_send_message : discord.Message | None = self.last_sent_data.get(message.channel.id)
            if last_send_message:
                if message.id != last_send_message.id:
                    try:
                        await last_send_message.delete()
                    except discord.NotFound:
                        return
                    new_last_sent = await message.channel.send(self.only_media)
                    self.last_sent_data[message.channel.id] = new_last_sent 


    @commands.Cog.listener("on_reaction_add")
    async def reaction_add_listener(
        self, reaction: discord.Reaction, user: discord.Member | discord.User
    ) -> None:
        if reaction.is_custom_emoji() and isinstance(reaction.emoji, discord.Emoji):
            if (
                reaction.emoji.id == self.bot.custom_emoji_id
                and reaction.message.id not in self.already_added
                and reaction.count == 3
            ):
                channel = reaction.message.guild.get_channel(self.bot.catboard)
                if reaction.message.reference and not reaction.message.flags.forwarded:
                    replied_message = (
                        reaction.message.reference.cached_message
                        or reaction.message.reference.resolved
                    )
                    replied_content = (
                        replied_message.content
                        if len(replied_message.content) < 24
                        else f"{replied_message.content[0:21]}..."
                    )
                    embed = discord.Embed(
                        title="",
                        description=f"-# <:reply:{self.bot.reply_emoji_id}> [@{replied_message.author}](https://discord.com/users/{replied_message.author.id}): `{replied_content}`\
                                        \n**[@{reaction.message.author}](https://discord.com/users/{reaction.message.author.id})**: {reaction.message.content}",
                        timestamp=discord.utils.utcnow(),
                        color=reaction.message.author.top_role.color,
                    )
                    embed.set_author(
                        name=f"@{reaction.message.author}",
                        icon_url=reaction.message.author.display_avatar.url,
                    )
                else:
                    embed = discord.Embed(
                        title="",
                        description=f"{reaction.message.content}",
                        color=reaction.message.author.top_role.color,
                        timestamp=discord.utils.utcnow(),
                    )
                    embed.set_author(
                        name=f"@{reaction.message.author} said...", icon_url=reaction.message.author.display_avatar.url
                    )

                if reaction.message.attachments:
                    embed.set_image(url=reaction.message.attachments[0].url)

                await channel.send(
                    embed=embed, view=JumpToMessage(reaction.message.jump_url)
                )

                self.already_added.append(reaction.message.id)

    @commands.command(name="dm", description="DM a user")
    @commands.guild_only()
    @has_roles(admin=True)
    async def dm(
        self, ctx: commands.Context, member: discord.Member, *, message: str) -> None:
        if message is None:
            embed = discord.Embed(
                title="Message is Empty",
                description=f"- You cannot send a user an emtpy message.",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            return await ctx.send(embed=embed)
        try:
            await member.send(view=SayDmView(member, message, ctx.message.attachments if ctx.message.attachments else None))
        except discord.Forbidden:
            embed = discord.Embed(
                title="Unable to DM",
                description=f"- Unable to DM the member {member.mention}",
            )
            return await ctx.send(embed=embed)
        channel_embed = discord.Embed(
            title=f"✅ Successfully DMed `@{member}`", color=discord.Color.brand_green()
        )
        await ctx.send(embed=channel_embed, delete_after=5.0)

    @dm.error
    async def dm_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Invalid Input",
                description=f"\n- `!dm [user] [message]`",
                color=discord.Color.brand_red(),
            )
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="Member Not Found",
                description=f"- `{error.argument}` is not a member.",
                color=discord.Color.brand_red(),
            )
        else:
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"- {error}",
                color=discord.Color.brand_red(),
            )
        await ctx.send(embed=embed)

    @commands.command(name="say", description="Send a message in a channel")
    @commands.guild_only()
    @has_roles(appeal_staff=True)
    async def say(
        self, ctx: commands.Context, channel: discord.TextChannel | str, *, message: str = None) -> None:
        if message is None and channel and isinstance(channel, discord.TextChannel) or channel is None:
            embed = discord.Embed(
                title="Message is Empty",
                description=f"- You cannot send an emtpy message.",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            return await ctx.send(embed=embed)
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(view=SayDmView(channel, message, ctx.message.attachments if ctx.message.attachments else None))
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Unable to Send",
                    description=f"- Unable to send a message in {channel.mention}",
                )
                return await ctx.send(embed=embed)
        else:
            message = f"{channel} {message if message is not None else ""}"
            try:
                await ctx.send(view=SayDmView(ctx.channel, message, ctx.message.attachments if ctx.message.attachments else None))
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Unable to Send",
                    description=f"- Unable to send a message in {ctx.channel.mention}",
                )
                return await ctx.send(embed=embed)

        channel_embed = discord.Embed(
            title=f"✅ Successfully sent a message in {ctx.channel.mention}",
            color=discord.Color.brand_green(),
        )
        await ctx.send(embed=channel_embed, delete_after=5.0)

    @say.error
    async def say_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Invalid Input",
                description=f"\n- `!say [channel] [message]`",
                color=discord.Color.brand_red(),
            )
        elif isinstance(error, commands.MissingAnyRole):
            return
        elif isinstance(error, commands.ChannelNotFound):
            embed = discord.Embed(
                title="Channel Not Found",
                description=f"- `#{error.argument}` is not a text channel.",
                color=discord.Color.brand_red(),
            )
        else:
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"- {error}",
                color=discord.Color.brand_red(),
            )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utilities(bot))


class JumpToMessage(discord.ui.View):
    def __init__(self, url: str):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Jump to message!", style=discord.ButtonStyle.link, url=url
            )
        )

class DMContainer(discord.ui.Container):
    def __init__(self, member: discord.Member, message: str, attachments: list[discord.Attachment] | None = None):
        super().__init__()
        self.add_item(discord.ui.Section(f"## {member.guild.name}\
                                         \n>>> {message}", accessory=discord.ui.Thumbnail(member.guild.icon.url if member.guild.icon else "")))
        if attachments is not None:
            self.add_item(discord.ui.MediaGallery(*[discord.MediaGalleryItem(attachment.url) for attachment in attachments]))

class SayContainer(discord.ui.Container):
    def __init__(self, channel: discord.TextChannel, message: str, attachments: list[discord.Attachment] | None = None):
        super().__init__()
        self.add_item(discord.ui.Section(f"## {channel.guild.name}\
                                         \n>>> {message}", accessory=discord.ui.Thumbnail(channel.guild.icon.url if channel.guild.icon else "")))
        if attachments is not None:
            self.add_item(discord.ui.MediaGallery(*[discord.MediaGalleryItem(attachment.url) for attachment in attachments]))


class SayDmView(discord.ui.LayoutView):
    def __init__(self, messageable: discord.Member | discord.TextChannel, message: str,
                  attachments: list[discord.Attachment] | None = None):
        super().__init__(timeout=None)
        if isinstance(messageable, discord.Member):
            self.add_item(DMContainer(messageable, message, attachments))
        else:
            self.add_item(SayContainer(messageable, message, attachments)) 
