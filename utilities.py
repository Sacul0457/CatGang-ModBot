import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import time
from discord import app_commands

STICKY_CHANNEL = 1383545647977726062
SKULLBOARD_CHANNEL = 1381029891641966632
REPLY_EMOJI_ID = 1395943993593958473
CUSTOM_EMOJI_ID = 1319238323436388422 

MOD_LOG =  1350425247471636530 
NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
MODERATOR = 1319214233803816960
SENIOR = 1343556008223707156
ADMIN = (1319213465390284860, 1343556153657004074, 1356640586123448501, 1343579448020308008)
SACUL = 1294291057437048843
GUILD_ID = 1319213192064536607
class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
        self.last_sent_data = 0
        self.already_added = []

    async def cog_load(self):
        channel = await self.bot.fetch_channel(STICKY_CHANNEL)
        last_sent_message = await channel.send(embed=self.embed)
        self.last_sent_data = last_sent_message

    @commands.Cog.listener("on_message")
    async def sticky_message_listener(self, message: discord.Message):
        if message.channel.id == STICKY_CHANNEL:
            last_send_message: discord.Message = self.last_sent_data
            if last_send_message:
                if message.id != last_send_message.id:
                    try:
                        await last_send_message.delete()
                    except discord.NotFound as e:
                        return
                    new_last_sent = await message.channel.send(embed=self.embed)
                    self.last_sent_data = new_last_sent

    @commands.Cog.listener("on_reaction_add")
    async def reaction_add_listener(
        self, reaction: discord.Reaction, user: discord.Member | discord.User
    ) -> None:
        if reaction.is_custom_emoji():
            if (
                reaction.emoji.id == CUSTOM_EMOJI_ID
                and reaction.message.id not in self.already_added
                and reaction.count == 1
            ):
                channel = reaction.message.guild.get_channel(SKULLBOARD_CHANNEL)
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
                        description=f"-# <:reply:{REPLY_EMOJI_ID}> [@{replied_message.author}](https://discord.com/users/{replied_message.author.id}): `{replied_content}`\
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
                        name=f"@{user} said...", icon_url=user.display_avatar.url
                    )

                if reaction.message.attachments:
                    embed.set_image(url=reaction.message.attachments[0].url)

                await channel.send(
                    embed=embed, view=JumpToMessage(reaction.message.jump_url)
                )

                self.already_added.append(reaction.message.id)

    @commands.command(name="dm", description="DM a user")
    @commands.guild_only()
    @commands.has_any_role(*ADMIN)
    async def dm(
        self, ctx: commands.Context, member: discord.Member, *, message: str) -> None:
        await ctx.message.delete()
        if message is None:
            embed = discord.Embed(
                title="Message is Empty",
                description=f"- You cannot send a user an emtpy message.",
                color=discord.Color.brand_red(),
                timestamp=discord.utils.utcnow(),
            )
            return await ctx.send(embed=embed)
        embed = discord.Embed(
            title="", description=f"{message}", color=ctx.author.top_role.color
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        try:
            await member.send(embed=embed)
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
    @commands.has_any_role(*ADMIN)
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
            embed = discord.Embed(
                title="", description=f"{message}", color=ctx.author.top_role.color
            )
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Unable to Send",
                    description=f"- Unable to send a message in {channel.mention}",
                )
                return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="", description=f"{channel} {message if message is not None else ""}", color=ctx.author.top_role.color
            )
            try:
                await ctx.send(embed=embed)
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
