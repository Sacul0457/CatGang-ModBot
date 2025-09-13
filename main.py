import discord
from discord.ext import commands
from discord import app_commands
import asqlite
import os
from discord.utils import MISSING
from dotenv import load_dotenv
load_dotenv()
import asyncio
from paginator import ButtonPaginator
import typing
from functions import save_to_appealdb, delete_from_appealdb, execute_sql


TOKEN = os.getenv("TOKEN")
STAFF_ROLE = 1336377690168758342

cogs = ("mod", "logs", "automod", "utilities", "appeals")

async def main():
    async with asqlite.connect("mod.db") as conn:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS moddb(
                           case_id TEXT PRIMARY KEY, 
                           user_id INTEGER,
                           action TEXT,
                           mod_id INTEGER,
                           time FLOAT,
                           log_id INTEGER) """)
        await conn.execute("""CREATE INDEX IF NOT EXISTS user_id_index on moddb(user_id)""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS mod_id_index on moddb(mod_id)""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS time_index on moddb(time)""")

        await conn.execute(
            """CREATE TABLE IF NOT EXISTS tempbandb(
                           user_id INTEGER PRIMARY KEY,
                           time FLOAT,
                           log_id INTEGER) """)
        await conn.execute("""CREATE INDEX IF NOT EXISTS time_index on tempbandb(time)""")

        await conn.execute('''CREATE TABLE IF NOT EXISTS appealdb(
                           thread_id INTEGER PRIMARY KEY,
                           user_id INTEGER,
                           action TEXT) ''')
        await conn.commit()


asyncio.run(main())


class ModBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.none()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.guild_messages = True
        intents.emojis_and_stickers = True
        intents.guild_reactions = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None,
        )
        self.spam_limit = commands.CooldownMapping.from_cooldown(
            5, 3.5, type=commands.BucketType.member
        )

    async def setup_hook(self):
        self.mod_pool = await asqlite.create_pool("mod.db", size=5)
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"Loaded: {cog}")
            except Exception as e:
                print(f"An error occurred: {e}")
        asyncio.get_event_loop().set_debug(True)

    async def close(self):
        await self.mod_pool.close()
        await super().close()


bot = ModBot()

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    pass

@app_commands.guild_only()
class Appeal(app_commands.Group):
    def __init__(self):
        super().__init__(name="appeal", description="Appeal debugging", default_permissions=discord.Permissions(manage_guild=True))
    @app_commands.command(name='info', description='Get info about an appeal')
    @app_commands.describe(thread = "The appeal to get info on")
    async def appeal_info(self, interaction: discord.Interaction, thread: discord.Thread) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)
        async with bot.mod_pool.acquire() as conn:
            row = await conn.execute('''SELECT user_id, action FROM appealdb WHERE thread_id = ?''',
                            (thread.id))
            result = await row.fetchone()

        if result is None:
            return await interaction.followup.send(f"Thread `{thread.id}` is not saved to the DB.")
        else:
            user_id = result['user_id']
            action = result['action']
            await interaction.followup.send(f"Showing results for thread: {thread.mention} (`{thread.id}`)\n```- User ID: {user_id}\n- Action: {action}```")    \
            

    @app_commands.command(name='add', description="To add an appeal manually")
    @app_commands.describe(thread = " The thread to add", user = "The user of the appeal", action = "The type of appeal")
    async def appeal_add(self, interaction: discord.Interaction, thread: discord.Thread, user: discord.User, action: typing.Literal['warn', 'ban', 'mute']) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)

        await save_to_appealdb(bot, thread.id, user.id, action)
        await interaction.followup.send(f"Successfully added {thread.id} to the DB. Values: \n- user_id: {user.id}\n- Action: {action}")


    @app_commands.command(name='remove', description="To remove an appeal from the db")
    @app_commands.describe(thread = "The thread to remove")
    async def appeal_remove(self, interaction: discord.Interaction, thread: discord.Thread) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)
        await delete_from_appealdb(bot, thread.id)
        await interaction.followup.send(f"Successfully removed {thread.id} from the DB.")


class Cog(app_commands.Group):
    def __init__(self):
        super().__init__(name="cog", description="Cog debugging", default_permissions=discord.Permissions(administrator=True))


    @app_commands.command(name='load', description='Load a cog')
    @app_commands.describe(cog = "The cog to load")
    async def cog_load(self, interaction: discord.Interaction, cog: typing.Literal['appeals', 'mod', 'logs', 'utilities', 'automod']) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)

        await bot.load_extension(cog)
        await interaction.followup.send(f"Successfully loaded: {cog}")


    @app_commands.command(name='reload', description='Reload a cog')
    @app_commands.describe(cog = "The cog to reload")
    async def appeal_reload(self, interaction: discord.Interaction, cog: typing.Literal['appeals', 'mod', 'logs', 'utilities', 'automod']) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)
        await bot.reload_extension(cog)
        await interaction.followup.send(f"Successfully reloaded: {cog}")


    @app_commands.command(name='unload', description='Unload a cog')
    @app_commands.describe(cog = "The cog to unload")
    async def appeal_unload(self, interaction: discord.Interaction, cog: typing.Literal['appeals', 'mod', 'logs', 'utilities', 'automod']) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)
        await bot.unload_extension(cog)
        await interaction.followup.send(f"Successfully unloaded: {cog}")

@bot.tree.command(name='evalsql', description="Execute an sql query")
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(query = "The query to execute")
async def evalsql(interaction: discord.Interaction, query: str):
    await interaction.response.defer(ephemeral=True)
    try:
        result = await execute_sql(query)
    except Exception as e:
        return await interaction.followup.send(f"An error occurred: {e}")
    await interaction.followup.send(f"Result: ```json\n{result}```")

@bot.command()
@commands.has_role(STAFF_ROLE)
async def help(ctx: commands.Context, feature: typing.Optional[str] = None) -> None:
    if feature is None:
        description1 = f">>> - `!ban [user] [duration] [reason]`\n- `!unban [user] [reason]`\n- `!kick [user] [reason]`\
                        \n- `!mute [user] [duration] [reason]`\n- `!unmute [user] [reason]`\
                        \n- `!warn [user] [reason]`\n- `!deletewarns [user] [reason]`\n- `!unwarn [case_id] [reason]`\
                        \n- `!slowmode [duration] [channel]`\
                        \n- `!clean [limit]` \n- `!lock [channel] [reason]` \n- `!unlock [channel] [reason]`"
        embed1 = discord.Embed(
            title="Moderation Commands",
            description=description1,
            color=discord.Color.blurple(),
        )
        embed1.set_footer(text=f"Use !help [command] for more information")

        description2 = f">>> - `!case [case_id]`\n- `!caselist user [user]`\n- `!caselist mod [user]`\n- `!deletecase [case_id]`\
                        \n- `!cases`"
        embed2 = discord.Embed(
            title="Case Commands",
            description=description2,
            color=discord.Color.blurple(),
        )
        embed2.set_footer(text=f"Use !help [command] for more information.")

        description3 = f">>> - `!massban [users]`\n- `!masskick [users]` \n- `!massmute [users]`\n- `!massunban [users]`"
        embed3 = discord.Embed(
            title="Mass Commands",
            description=description3,
            color=discord.Color.blurple(),
        )
        embed3.set_footer(text=f"Use !help [command] for more information.")

        description4 = f">>> - `!dm [user] [message]`\n- `!say [channel] [message]`"
        embed4 = discord.Embed(
            title="Others", description=description4, color=discord.Color.blurple()
        )
        embed4.set_footer(text=f"Use !help [command] for more information.")
        button_pages = ButtonPaginator([embed1, embed2, embed3, embed4])
        await button_pages.start(ctx.channel)
    else:
        if feature.lower() == "ban":
            embed = discord.Embed(
                title="Ban Command", description="Ban a user or ban them temporarily."
            )
            embed.add_field(name="Usage", value=f"- `!ban [user] [duration] [reason]`")
            embed.add_field(
                name="Example",
                value=f"- `!ban @Sacul Spamming`\n- `!ban @Sacul 24h,10d Spamming`",
                inline=False,
            )

        elif feature.lower() == "unban":
            embed = discord.Embed(title="Unban Command", description="Unban a user")
            embed.add_field(name="Usage", value=f"- `!unban [user] [reason]`")
            embed.add_field(
                name="Example",
                value=f"- `!unban 802167689011134474 Appealed`",
                inline=False,
            )

        elif feature.lower() == "mute":
            embed = discord.Embed(
                title="Mute Command", description="Mute a user (Max 28 days)"
            )
            embed.add_field(name="Usage", value=f"- `!mute [user] [duration] [reason]`")
            embed.add_field(
                name="Example",
                value=f"- `!mute @Sacul 2h Spamming`\n- `!mute @Sacul 50m,30s Flooding`",
                inline=False,
            )

        elif feature.lower() == "unmute":
            embed = discord.Embed(title="Unmute Command", description="Unmute a user")
            embed.add_field(name="Usage", value=f"- `!unmute [user] [reason]`")
            embed.add_field(
                name="Example", value=f"- `!unmute @Sacul Appealed`", inline=False
            )

        elif feature.lower() == "kick":
            embed = discord.Embed(title="Kick Command", description="Kick a user")
            embed.add_field(name="Usage", value=f"- `!kick [user] [reason]`")
            embed.add_field(
                name="Example", value=f"- `!kick @Sacul NSFW`", inline=False
            )

        elif feature.lower() == "warn":
            embed = discord.Embed(title="Warn Command", description="Warn a user")
            embed.add_field(name="Usage", value=f"- `!warn [user] [reason]`")
            embed.add_field(
                name="Example", value=f"- `!warn @Sacul NSFW`", inline=False
            )

        elif feature.lower() == "deletewarns":
            embed = discord.Embed(
                title="Deletewarns Command",
                description="Remove all warns from a user (Excluding automod warns)",
            )
            embed.add_field(name="Usage", value=f"- `!deletewarns [user] [reason]`")
            embed.add_field(
                name="Example", value=f"- `!deletewarns @Sacul Appealed`", inline=False
            )

        elif feature.lower() == "unwarn":
            embed = discord.Embed(
                title="Unwarn Command",
                description="Remove **a** warn from a user",
            )
            embed.add_field(name="Usage", value=f"- `!unwarn [case_id] [reason]`")
            embed.add_field(
                name="Example", value=f"- `!unwarn 1234abcd Appealed`", inline=False
            )

        elif feature.lower() == "slowmode":
            embed = discord.Embed(
                title="Slowmode Command",
                description="Set slowmode to a channel (Max 6 hours)",
            )
            embed.add_field(name="Usage", value=f"- `!slowmode [duration] [channel]`")
            embed.add_field(
                name="Example",
                value=f"- `!slowmode 2h`\n- `!slowmode 50m,30s #general`",
                inline=False,
            )
        elif feature.lower() == "lock":
            embed = discord.Embed(
                title="Lock Command",
                description="Lock a channel",
            )
            embed.add_field(name="Usage", value=f"- `!lock [channel] [reason]`")
            embed.add_field(
                name="Example",
                value=f"- `!lock Raiding`\n- `!slowmode #general raid`",
                inline=False,
            )
        elif feature.lower() == "unlock":
            embed = discord.Embed(
                title="Unlock Command",
                description="Unlock a channel",
            )
            embed.add_field(name="Usage", value=f"- `!unlock [channel] [reason]`")
            embed.add_field(
                name="Example",
                value=f"- `!unlock Raid ended`\n- `!unlock #general raid ended`",
                inline=False,
            )
        elif feature.lower() == "say":
            embed = discord.Embed(
                title="Say Command", description="Send a message to a channel"
            )
            embed.add_field(name="Usage", value=f"- `!say [channel] [message]`")
            embed.add_field(
                name="Example",
                value=f"- `!say Hai there`\n- `!say #general Bai bai`",
                inline=False,
            )

        elif feature.lower() == "dm":
            embed = discord.Embed(
                title="DM Command", description="Send a message to a member"
            )
            embed.add_field(name="Usage", value=f"- `!dm [user] [message]`")
            embed.add_field(
                name="Example", value=f"- `!dm @Sacul Hai there`", inline=False
            )

        elif feature.lower() == "clean":
            embed = discord.Embed(
                title="Clean Command",
                description="Clean/Purge messages (Max 800 messages)",
            )
            embed.add_field(name="Usage", value=f"- `!clean [limit] [channel]`")
            embed.add_field(
                name="Example",
                value=f"- `!clean 50`\n- `!clean 30 #general`",
                inline=False,
            )

            embed2 = discord.Embed(
                title="Clean Until Command",
                description="Clean/Purge messages until a certain message (Max 800 messages)",
            )
            embed2.add_field(name="Usage", value=f"- `!clean until [msg] [channel]`")
            embed2.add_field(
                name="Example",
                value=f"- `!clean until 1395921533049901126`\n- `!clean until [msglink]`",
                inline=False,
            )

            embed3 = discord.Embed(
                title="Clean Between Command",
                description="Clean/Purge messages between two messages (Max 800 messages)",
            )
            embed3.add_field(
                name="Usage", value=f"- `!clean between [msg1] [msg2] [channel]`"
            )
            embed3.add_field(
                name="Example",
                value=f"- `!clean between 1395921533049901126 1395925327934394440`\n- `!clean between [msglink1] [msglink2]`",
                inline=False,
            )
            clean_paginator = ButtonPaginator([embed, embed2, embed3])
            await clean_paginator.start(ctx.channel)
            return

        elif "mass" in feature.lower():
            embed = discord.Embed(
                title="Massban Command", description="Ban multiple users at once"
            )
            embed.add_field(name="Usage", value=f"- `!massban [users]`")
            embed.add_field(
                name="Example",
                value=f"- `!massban @Sacul @Bot`\n- `!massban 802167689011134474 1355197988988915915`",
                inline=False,
            )

            embed2 = discord.Embed(
                title="Massunban Command", description="Unban multiple users at once"
            )
            embed2.add_field(name="Usage", value=f"- `!massunban [users]`")
            embed2.add_field(
                name="Example",
                value=f"- `!massunban 802167689011134474 1355197988988915915`",
                inline=False,
            )

            embed3 = discord.Embed(
                title="Masskick Command", description="Kick multiple users at once"
            )
            embed3.add_field(name="Usage", value=f"- `!masskick [users]`")
            embed3.add_field(
                name="Example",
                value=f"- `!masskick @Sacul @Bot`\n- `!masskick 802167689011134474 1355197988988915915`",
                inline=False,
            )

            embed4 = discord.Embed(
                title="Massmute Command", description="Mute multiple users at once"
            )
            embed4.add_field(name="Usage", value=f"- `!massmute [users]`")
            embed4.add_field(
                name="Example",
                value=f"- `!massmute @Sacul @Bot`\n- `!massmute 802167689011134474 1355197988988915915`",
                inline=False,
            )
            if feature.lower() == "massunban":
                pages = [embed2, embed, embed3, embed4]
            elif feature.lower() == "massmute":
                pages = [embed4, embed, embed3, embed2]
            elif feature.lower() == "masskick":
                pages = [embed3, embed4, embed2, embed]
            else:
                pages = [embed, embed2, embed3, embed4]
            clean_paginator = ButtonPaginator(pages)
            await clean_paginator.start(ctx.channel)
            return

        elif "case" in feature.lower():
            embed = discord.Embed(
                title="Case Command", description="Get information about a case"
            )
            embed.add_field(name="Usage", value=f"- `!case [case_id]`")
            embed.add_field(
                name="Example", value=f"- `!case 0oMJnWkNTcSs9VjOsIE3Zg`", inline=False
            )

            embed2 = discord.Embed(
                title="Caselist User Command", description="Get all the cases of a user"
            )
            embed2.add_field(name="Usage", value=f"- `!caselist user [user]`")
            embed2.add_field(
                name="Example", value=f"- `!caselist user @Sacul`", inline=False
            )

            embed3 = discord.Embed(
                title="Caselist Mod Command", description="Get all cases of a moderator"
            )
            embed3.add_field(name="Usage", value=f"- `!caselist mod [user]`")
            embed3.add_field(
                name="Example", value=f"- `!caselist mod @Sacul`", inline=False
            )

            embed4 = discord.Embed(
                title="Deletecase Command", description="Delete a case"
            )
            embed4.add_field(name="Usage", value=f"- `!deletecase [case_id]`")
            embed4.add_field(
                name="Example",
                value=f"- `!deletecase 0oMJnWkNTcSs9VjOsIE3Zg`",
                inline=False,
            )

            embed5 = discord.Embed(
                title="Cases Command", description="Show the last 30 cases"
            )
            embed5.add_field(name="Usage", value=f"- `!cases`")
            embed5.add_field(
                name="Example",
                value=f"- `!cases`",
                inline=False,
            )

            if feature.lower() == "caselist":
                pages = [embed2, embed3, embed4, embed5, embed]
            elif "delete" in feature.lower():
                pages = [embed4, embed3, embed2, embed5, embed]
            elif "cases" in feature:
                pages = [embed5, embed4, embed3, embed2, embed]
            else:
                pages = [embed, embed2, embed3, embed4, embed5]

            case_paginator = ButtonPaginator(pages)
            await case_paginator.start(ctx.channel)
            return

        else:
            embed = discord.Embed(
                title="No Command Found",
                description=f"- There is no such command `{feature}`",
                color=discord.Color.brand_red(),
            )
        await ctx.send(embed=embed)


bot.run(TOKEN)
