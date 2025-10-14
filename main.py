import discord
from discord.ext import commands
from discord import app_commands
import asqlite
import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
from paginator import ButtonPaginator
import typing
from functions import save_to_appealdb, delete_from_appealdb, execute_sql
import aiofiles
from pathlib import Path
import psutil
import time

from json import loads, dumps
BASE_DIR = Path(__file__).parent

# Build full path to the file
CONFIG_PATH = BASE_DIR / "config.json"
TOKEN = os.getenv("TOKEN")
STAFF_ROLE = 1424837947177570416

cogs = ("mod", "logs", "automod", "utilities", "appeals", "reports")


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
        await self.setup_config()
        self.mod_pool = await asqlite.create_pool("mod.db", size=5)

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"Loaded: {cog}")
            except Exception as e:
                print(f"An error occurred: {e}")
        asyncio.get_event_loop().set_debug(True)
        self.tree.add_command(Appeal())
        self.tree.add_command(Cog())

    async def close(self):
        await self.mod_pool.close()
        await super().close()


    def get_message(self, id: int, /) -> typing.Optional[discord.Message]:
        """Returns a message from the cache if found."""
        return discord.utils.find(lambda m: m.id == id, reversed(self.cached_messages)) if self.cached_messages else None
    
    async def setup_config(self):
        async with aiofiles.open(CONFIG_PATH, 'r') as f:
            data = await f.read()
            data = loads(data)

        roles_data = data['roles']
        channel_guild_data = data['channel_guild']
        other_data = data['others']
        self.mod = roles_data['MOD']
        self.appeal_staff = roles_data['APPEAL_STAFF']
        self.admin = roles_data['ADMIN']
        self.sacul = roles_data['SACUL']
        self.senior = roles_data['SENIOR']
        self.appeal_staff_leader = roles_data['APPEAL_STAFF_LEADER']
        self.main_guild_id = channel_guild_data['GUILD_ID']
        self.mod_log = channel_guild_data['MOD_LOG']
        self.appeal_server = channel_guild_data['APPEAL_SERVER'] 
        self.appeal_channel = channel_guild_data['APPEAL_CHANNEL']
        self.event_logs = channel_guild_data['EVENT_LOGS']
        self.black_listed_channels = channel_guild_data['BLACK_LISTED_CHANNELS']
        self.management_categories = channel_guild_data['MANAGEMENT_CATEGORIES']
        self.management = channel_guild_data['MANAGEMENT']
        self.private_log = channel_guild_data['PRIVATE_LOG']
        self.report_channel = channel_guild_data['REPORT_CHANNEL']
        self.media_category_id = channel_guild_data['MEDIA_CATEGORY_ID']
        self.sticky_channel = channel_guild_data['STICKY_CHANNEL']
        self.catboard = channel_guild_data['CATBOARD']
        self.reply_emoji_id = channel_guild_data['REPLY_EMOJI_ID']
        self.custom_emoji_id = channel_guild_data['CUSTOM_EMOJI_ID']
        self.sticky_channels: list[int] = channel_guild_data['STICKY_CHANNELS']


        self.numbers = other_data['NUMBERS']


bot = ModBot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.TransformerError):
        if error.transformer.type == discord.AppCommandOptionType.user:
            embed = discord.Embed(title="Member Not Found",
                                  description=f"- `{error.value}` is not a member.",
                                  color=discord.Colour.brand_red())
        else:
            embed = discord.Embed(title="Transformer Error",
                                  description=f"- {error}",
                                  color=discord.Colour.brand_red())
    elif isinstance(error, app_commands.MissingAnyRole):
        pass
    else:
        embed = discord.Embed(title="An Error Occurred",
                              description=f"- {error}\n-# The developer has been notified",
                              color=discord.Color.brand_red())
        await handle_interaction_error(error, interaction)
    if not interaction.is_expired() and not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)

async def handle_interaction_error(error: commands.CommandError|app_commands.AppCommandError, interaction: discord.Interaction | None = None) -> None:
    error_channel = bot.get_channel(1425795763627098233)
    if error_channel is None:
        return
    content = f"Error: `{error}`"

    if interaction:
        interaction_created_at = interaction.created_at.timestamp()
        now = time.time()
        interaction_data = interaction.data or {}
        content += f"\n### Interaction Error:\n>>> Interaction created at <t:{round(interaction_created_at)}:T> ({now - interaction_created_at:.3f}s ago)\
            \nUser: {interaction.user.mention} | Channel: {getattr(interaction.channel, 'mention', f"Unknown channel ({interaction.channel_id})")} | Type: {interaction.type.name}"
        if interaction.command and interaction.type is discord.InteractionType.application_command and interaction_data:
            command_id = interaction_data.get('id', 0)
            if interaction.command.parent:
                try:
                    options_dict = interaction_data.get("options", [])[0].get("options", []) # This is nested since it is a sub command
                    command_mention = f"</{interaction.command.qualified_name}:{command_id}>"
                except (IndexError, AttributeError):
                    options_dict  = interaction_data.get("options", [])
                    command_mention = f"</{interaction.command.name}:{command_id}>"
            else:
                options_dict  = interaction_data.get("options", [])
                command_mention = f"</{interaction.command.name}:{command_id}>"
            content += f"\nCommand: {command_mention}, inputted values:"

            options_formatted = " \n".join([f"- {option.get('name', 'Unknown')}: {option.get('value', 'Unknown')}" for option in options_dict])
            content += f"\n```{options_formatted}```"
        else:
            content += f"\n```json\n{interaction_data}```"
        await error_channel.send(content)
    else:
        await error_channel.send(content=content)


@bot.command()
async def sync(ctx: commands.Context) -> None:
    if ctx.author.id != 802167689011134474:
        return
    await ctx.message.delete()
    synced = await bot.tree.sync()
    await ctx.send(f"Successfully synced {len(synced)} commands", delete_after=5.0)


@bot.command()
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def stats(ctx: commands.Context) -> None:
    cpu_count = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    total = int(memory.total / (1024 ** 3))
    available = int(memory.available / (1024 ** 3))
    percent = memory.percent
    used = int(memory.used / (1024 ** 3))
    embed = discord.Embed(title="Bot Stats",
                          description=f">>> - CPU Count: {cpu_count}\n- CPU: {cpu_percent}%\
                        \n- Total: {total}GB\n- Available: {available}GB\
                        \n- Used: {used}GB ({percent}%)",
                          color=discord.Color.blurple())
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)


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
                            (thread.id, ))
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


@app_commands.guild_only()
class Cog(app_commands.Group):
    def __init__(self):
        super().__init__(name="cog", description="Cog debugging", default_permissions=discord.Permissions(administrator=True))


    @app_commands.command(name='load', description='Load a cog')
    @app_commands.describe(cog = "The cog to load")
    async def cog_load(self, interaction: discord.Interaction, cog: typing.Literal['appeals', 'mod', 'logs', 'utilities', 'automod', 'reports']) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)

        await bot.load_extension(cog)
        await interaction.followup.send(f"Successfully loaded: {cog}")


    @app_commands.command(name='reload', description='Reload a cog')
    @app_commands.describe(cog = "The cog to reload")
    async def appeal_reload(self, interaction: discord.Interaction, cog: typing.Literal['appeals', 'mod', 'logs', 'utilities', 'automod', 'reports']) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)
        await bot.reload_extension(cog)
        await interaction.followup.send(f"Successfully reloaded: {cog}")


    @app_commands.command(name='unload', description='Unload a cog')
    @app_commands.describe(cog = "The cog to unload")
    async def appeal_unload(self, interaction: discord.Interaction, cog: typing.Literal['appeals', 'mod', 'logs', 'utilities', 'automod', 'reports']) -> None:
        if interaction.user.id != 802167689011134474:
            return
        await interaction.response.defer(ephemeral=True)
        await bot.unload_extension(cog)
        await interaction.followup.send(f"Successfully unloaded: {cog}")

@bot.tree.command(name='evalsql', description="Execute an sql query")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(query = "The query to execute")
async def evalsql(interaction: discord.Interaction, query: str):
    if interaction.user.id != 802167689011134474:
        return
    await interaction.response.defer(ephemeral=True)
    try:
        result = await execute_sql(query)
    except Exception as e:
        return await interaction.followup.send(f"An error occurred: {e}")
    await interaction.followup.send(f"Result: ```json\n{result}```")


class RoleModals(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Edit Roles", timeout=None, custom_id="edit_roles_modal")

        moderator_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.mod)
        senior_moderator_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.senior)
        admin_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.admin)
        appeal_staff_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.appeal_staff)
        all_roles = discord.ui.TextDisplay(f"### Current Configuration:\n>>> Moderator Roles: {moderator_roles}\
                                           \nSnr Moderator Roles: {senior_moderator_roles}\
                            \nAdmin Roles: {admin_roles}\nAppeal Staff Roles: {appeal_staff_roles}")

        self.role_type = discord.ui.Label(text="Role Type", description="What should this role be (e.g staff role, senior mod role etc)",
                                          component=discord.ui.Select(options=[discord.SelectOption(label="Moderator", value="mod"),
                                                                               discord.SelectOption(label="Senior Moderator", value="senior"),
                                                                               discord.SelectOption(label="Admin", value="admin"),
                                                                               ], required=True))
        self.roles = discord.ui.Label(text="New Role", description="What this role should be in the config",
                                      component=discord.ui.RoleSelect(max_values=5, min_values=1))
        
        self.add_item(all_roles)
        self.add_item(self.role_type)
        self.add_item(self.roles)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        assert(isinstance(self.role_type.component, discord.ui.Select))
        assert(isinstance(self.roles.component, discord.ui.RoleSelect))

        role_type = self.role_type.component.values[0]

        async with aiofiles.open(CONFIG_PATH, "r") as f:
            text = await f.read()
            data = loads(text)

        
        chosen_roles = [role.id for role in self.roles.component.values]
        data['roles'][f"{role_type.upper()}"] = chosen_roles

        async with aiofiles.open(CONFIG_PATH, "w") as f:
            to_write = dumps(data, indent=3)
            await f.write(to_write)
            

        role_mentions = ",".join([f"<@&{role_id}>" for role_id in chosen_roles])
        embed = discord.Embed(title="Role Config Updated",
                              description=f"- {role_mentions} is now the `{role_type.upper()}` role.",
                              color=discord.Color.brand_green())
        await interaction.followup.send(embed=embed, ephemeral=True)
        setattr(bot, role_type, chosen_roles)


class ChannelModals(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Edit Channels", timeout=None, custom_id="edit_channel_modal")

        mod_log = (f"<#{bot.mod_log}>")
        event_logs = (f"<#{bot.event_logs}>")
        management_logs = (f"<#{bot.management}>")
        appeal_channel = (f"<#{bot.appeal_channel}>")
        private_log = (f"<#{bot.private_log}>")
        all_channels = discord.ui.TextDisplay(f"### Current Config:\n>>> Mod Log: {mod_log}\nEvent Log: {event_logs}\
                                              \nManagement Log: {management_logs}\nAppeal Channel: {appeal_channel}\
                                              \nPrivate Log: {private_log}")

        self.channel_type = discord.ui.Label(text="Channel Type", description="What should this channel be (e.g logs, mod logs etc)",
                                          component=discord.ui.Select(options=[discord.SelectOption(label="Mod Logs", value="mod_log"),
                                                                               discord.SelectOption(label="Appeal Channel", value="appeal_channel"),
                                                                               discord.SelectOption(label="Event Logs", value="event_logs"),
                                                                               discord.SelectOption(label="Management Logs", value="management"),
                                                                               discord.SelectOption(label="Private Log", value="private_log")
                                                                               ], required=True))
        self.channels = discord.ui.Label(text="New Channel", description="What this channel should be in the config",
                                      component=discord.ui.ChannelSelect(max_values=1, min_values=1, channel_types=[discord.ChannelType.text]))
        
        self.add_item(all_channels)
        self.add_item(self.channel_type)
        self.add_item(self.channels)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        assert(isinstance(self.channel_type.component, discord.ui.Select))
        assert(isinstance(self.channels.component, discord.ui.ChannelSelect))
        channel_type = self.channel_type.component.values[0]


        async with aiofiles.open(CONFIG_PATH, "r") as f:
            text = await f.read()
            data = loads(text)

        chosen_channel = self.channels.component.values[0].id
        data['channel_guild'][channel_type.upper()] = chosen_channel

        async with aiofiles.open(CONFIG_PATH, "w") as f:
            to_write = dumps(data, indent=3)
            await f.write(to_write)
            
        embed = discord.Embed(title="Channel Config Updated",
                              description=f"- <#{chosen_channel}> is now the `{channel_type}` channel.",
                              color=discord.Color.brand_green())
        await interaction.followup.send(embed=embed, ephemeral=True)
        setattr(bot, channel_type, chosen_channel)


class ConfigContainer(discord.ui.Container):
    def __init__(self, children: list[discord.ui.Item]) -> None:
        super().__init__(*children)

class EditRoleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Edit", custom_id="edit_roles_button")

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(RoleModals())

class EditChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Edit", custom_id="edit_channels_button")

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(ChannelModals())

class ShowConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="View", custom_id="show_config_button")

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        moderator_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.mod)
        senior_moderator_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.senior)
        admin_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.admin)
        appeal_staff_roles = ", ".join(f"<@&{role_id}>" for role_id in bot.appeal_staff)

        mod_log = (f"<#{bot.mod_log}>")
        event_logs = (f"<#{bot.event_logs}>")
        management_logs = (f"<#{bot.management}>")
        appeal_channel = (f"<#{bot.appeal_channel}>")

        embed = discord.Embed(title="Configs")
        embed.add_field(name="Roles",
                        value=f">>> Moderator Roles: {moderator_roles}\nSnr Moderator Roles: {senior_moderator_roles}\
                            \nAdmin Roles: {admin_roles}\nAppeal Staff Roles: {appeal_staff_roles}")
        embed.add_field(name="Channels",
                        value=f">>> Mod Log: {mod_log}\nEvent Log: {event_logs}\nManagement Log: {management_logs}\nAppeal Channel: {appeal_channel}")

        
        await interaction.followup.send(embed=embed, ephemeral=True)

class ConfigView(discord.ui.LayoutView):
    def __init__(self, action: str) -> None:
        super().__init__(timeout=None)
        if action == "basic_config":
            header = discord.ui.TextDisplay("## Config Menu")
            separator1 = discord.ui.Separator()
            edit_role_accessory = discord.ui.Section("Role Configs", accessory=EditRoleButton())
            edit_channel_accessory = discord.ui.Section("Channel Configs", accessory=EditChannelButton())
            separator2 = discord.ui.Separator()
            show_config_accessory = discord.ui.Section("Current Configs", accessory=ShowConfigButton())

            self.add_item(ConfigContainer([header, separator1, edit_role_accessory, edit_channel_accessory, separator2, show_config_accessory]))

@bot.tree.command(description="Configure roles and channels")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
async def config(interaction: discord.Interaction):
    await interaction.response.send_message(view=ConfigView("basic_config"), ephemeral=True)


@bot.command()
@commands.guild_only()
@commands.has_role(STAFF_ROLE)
async def help(ctx: commands.Context, feature: typing.Optional[str] = None) -> None:
    if feature is None:
        description1 = f">>> - `/ban [user] [duration] [reason]`\n- `!unban [user] [reason]`\n- `!kick [user] [reason]`\
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