import discord
from discord.ext import commands
import asyncio
import datetime
import time
import timeit
import json
MOD_LOG =  1350425247471636530  
MANAGEMENT =1350425247471636530 

class LogCogs(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_message_delete")
    async def message_delete_listener(self, message:discord.Message):
        if message.author.id == self.bot.user.id:
            return
        embed = discord.Embed(title="Message Deleted",
                              description=f"> **User:** {message.author.mention} ({message.author.id})\n> **Channel:** {message.channel.mention}\
                                \n> **Sent:** <t:{int(message.created_at.timestamp())}:R>\n**Content**{f"\n>>> {message.content}" if message.content else ": No Content."}",
                                color=discord.Color.brand_red(),
                                timestamp=discord.utils.utcnow())
        embed.set_author(name=f"@{message.author}", icon_url=message.author.display_avatar.url)
        async for entry in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
            if entry.target.id == message.author.id:
                mod = message.guild.get_member(entry.user_id)
                embed.set_footer(text=f"Deleted by @{mod}", icon_url=mod.display_avatar.url)
                break
        channel = self.bot.get_channel(MOD_LOG)
        if message.attachments:
            await channel.send(embed=embed, files=[await image.to_file() for image in message.attachments])
        else:
            await channel.send(embed=embed)
    @commands.Cog.listener("on_message_edit")
    async def message_edit_listener(self, before_edit:discord.Message, after_edit:discord.Message):
        if before_edit.author == self.bot:
            return
        if before_edit.content == after_edit.content:
            return
        embed = discord.Embed(title="Message Edited",
                              description=f">>> **User:** {after_edit.author.mention} ({after_edit.author.id})\n**Channel:** {after_edit.channel.mention}\
                                \n**Sent:** <t:{int(after_edit.created_at.timestamp())}:R>",
                                color=discord.Color.orange(),
                                timestamp=discord.utils.utcnow())
        embed.add_field(name="Before",
                        value=f">>> {f"{before_edit.content[:1017]}..." if len(before_edit.content) > 1023 else before_edit.content}")
        embed.add_field(name="After",
                        value=f">>> {f"{after_edit.content[:1017]}..." if len(after_edit.content) > 1023 else after_edit.content}", inline=False)
        embed.set_author(name=f"@{after_edit.author}", icon_url=after_edit.author.display_avatar.url)
        channel = self.bot.get_channel(MOD_LOG)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_bulk_message_delete")
    async def bulk_message_delete_listener(self, messages:list[discord.Message]):
        embed = discord.Embed(title="Bulk Message Delete",
                              description=f"- {len(messages)} messages were bulk deleted in {messages[0].channel.mention}",
                                color=discord.Color.brand_red(),
                                timestamp=discord.utils.utcnow())
        async for entry in messages[0].guild.audit_logs(action=discord.AuditLogAction.message_bulk_delete, limit=3):
            if entry.target.id == messages[0].channel.id:
                mod = messages[0].guild.get_member(entry.user_id)
                embed.set_footer(text=f"Deleted by @{mod}", icon_url=mod.display_avatar.url)
                break
        channel = self.bot.get_channel(MOD_LOG)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_member_update")
    async def member_update_listener(self, before_member:discord.Member, after_member:discord.Member):
        if before_member.roles != after_member.roles:
            if len(after_member.roles) > len(before_member.roles):
                role_added : list[discord.Role] = [role for role in after_member.roles if role not in before_member.roles and role != after_member.guild.default_role]
                embed = discord.Embed(title="Role Added",
                                      description=f"{after_member.mention} has been given the {role_added[0].mention if len(role_added) <1 else ", ".join(f"{role_added[i].mention}" for i in range(len(role_added)))} role.",
                                      color=discord.Color.brand_green(),
                                      timestamp=discord.utils.utcnow())
                embed.set_author(name=f"@{after_member}", icon_url=after_member.display_avatar.url)
                async for entry in after_member.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                    if entry.target.id == after_member.id:
                        mod = after_member.guild.get_member(entry.user_id)
                        embed.set_footer(text=f"Added by @{mod}", icon_url=mod.display_avatar.url)
                        break
            else:
                role_removed : list[discord.Role] = [role for role in before_member.roles if role not in after_member.roles and role != after_member.guild.default_role]
                embed = discord.Embed(title="Role Removed",
                                      description=f"{after_member.mention} has been removed from the {role_removed[0].mention if len(role_removed) <1 else ", ".join(f"{role_removed[i].mention}" for i in range(len(role_removed)))} role",
                                      color=discord.Color.brand_red(),
                                      timestamp=discord.utils.utcnow())
                embed.set_author(name=f"@{after_member}", icon_url=after_member.display_avatar.url)
                async for entry in after_member.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                    if entry.target.id == after_member.id:
                        mod = after_member.guild.get_member(entry.user_id)
                        embed.set_footer(text=f"Removed by @{mod}", icon_url=mod.display_avatar.url)
                        break
            channel = self.bot.get_channel(MANAGEMENT)
            await channel.send(embed=embed)
        elif before_member.nick != after_member.nick:
            embed = discord.Embed(title="Nickname Change",
                                description=f">>> **User:** {after_member.mention} ({after_member.id})\
                                    \n**New:** {after_member.display_name}\n**Old:** {before_member.display_name}",
                                    color=discord.Color.orange())
            embed.set_author(name=f"@{after_member}", icon_url=after_member.display_avatar.url)
            embed.set_thumbnail(url=after_member.display_avatar.url)
            async for entry in after_member.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=3):
                if entry.target.id == after_member.id:
                    mod = after_member.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Changed by @{mod}", icon_url=mod.display_avatar.url)
                    break
            channel = self.bot.get_channel(MOD_LOG)
            await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_role_create")
    async def guild_role_create_listener(self, role:discord.Role):
        channel = self.bot.get_channel(MANAGEMENT)
        embed = discord.Embed(title="Role Created",
                              description=f"A new role {role.mention} has been created.",
                              color=discord.Color.brand_green(),
                              timestamp=discord.utils.utcnow())
        async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_create, limit=1):
            if entry.target.id == role.id:
                mod = role.guild.get_member(entry.user_id)
                embed.set_footer(text=f"Created by @{mod}", icon_url=mod.display_avatar.url)
                break
        await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_role_delete")
    async def guild_role_create_delete(self, role:discord.Role):
        channel = self.bot.get_channel(MANAGEMENT)
        embed = discord.Embed(title="Role Deleted",
                              description=f"The role `{role.name}` has been deleted.",
                              color=discord.Color.brand_red(),
                              timestamp=discord.utils.utcnow())
        async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
            if entry.target.id == role.id:
                mod = role.guild.get_member(entry.user_id)
                embed.set_footer(text=f"Deleted by @{mod}", icon_url=mod.display_avatar.url)
                break
        await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_role_update")
    async def guild_role_update_listener(self, before_role:discord.Role, after_role:discord.Role):

        if not before_role.hoist and after_role.hoist:
            embed = discord.Embed(title="Role Hoisted",
                                  description=f"The {after_role.mention} role has been hoisted.",
                                  timestamp=discord.utils.utcnow(),
                                  color=discord.Color.blurple())
            async for entry in after_role.guild.audit_logs(action=discord.AuditLogAction.role_update, limit=1):
                if entry.target.id == after_role.id:
                    mod = after_role.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Hoisted by @{mod}", icon_url=mod.display_avatar.url)
                    break
            channel = self.bot.get_channel(MANAGEMENT)
            await channel.send(embed=embed)
        elif before_role.hoist and not after_role.hoist:
            embed = discord.Embed(title="Role Unhoisted",
                                  description=f"The {after_role.mention} role has been unhoisted.",
                                  timestamp=discord.utils.utcnow(),
                                  color=discord.Color.blurple())
            async for entry in after_role.guild.audit_logs(action=discord.AuditLogAction.role_update, limit=1):
                if entry.target.id == after_role.id:
                    mod = after_role.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Unhoisted by @{mod}", icon_url=mod.display_avatar.url)
                    break
            channel = self.bot.get_channel(MANAGEMENT)
            await channel.send(embed=embed)
        elif before_role.permissions != after_role.permissions:
            channel = self.bot.get_channel(MANAGEMENT)
            before_perms_true = {name for name, value in before_role.permissions if value}
            after_perms_true = {name for name, value in after_role.permissions if value}

            before_perms_false = {name for name, value in before_role.permissions if not value}
            after_perms_false = {name for name, value in after_role.permissions if not value}


            added = after_perms_true - before_perms_true
            removed = after_perms_false - before_perms_false

            embed = discord.Embed(title="Role Permissions Update",
                                  description=f"The {after_role.mention} role has been updated.",
                                  color=discord.Color.blurple(),
                                  timestamp=discord.utils.utcnow())
            if added:
                new_perms = "\n- ".join(f"{perm}" for perm in added)
                embed = embed.add_field(name=f"Added [{len(added)}]",
                                      value=f">>> - {new_perms}")
            if removed:
                removed_perms = "\n- ".join(f"{perm}" for perm in removed)
                embed.add_field(name=f"Removed [{len(removed)}]",
                                    value=f"\n>>> - {removed_perms}",) 
            async for entry in after_role.guild.audit_logs(action=discord.AuditLogAction.role_update, limit=1):
                if entry.target.id == after_role.id:
                    mod = after_role.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Updated by @{mod}", icon_url=mod.display_avatar.url)
                    break
            await channel.send(embed=embed)
        elif before_role.color != after_role.color:
            embedafter = discord.Embed(title="Role Colour Change (New Colour)",
                                       description=f"The {after_role.mention} new role colour.",
                                       timestamp=discord.utils.utcnow(),
                                       color=after_role.color)
            embedbefore = discord.Embed(title="(Old Colour)",
                                       description=f"The {after_role.mention} old role colour.",
                                       timestamp=discord.utils.utcnow(),
                                       color=before_role.color)
            async for entry in after_role.guild.audit_logs(action=discord.AuditLogAction.role_update, limit=1):
                if entry.target.id == after_role.id:
                    mod = after_role.guild.get_member(entry.user_id)
                    embedafter.set_footer(text=f"Changed by @{mod}", icon_url=mod.display_avatar.url)
                    break
            channel = self.bot.get_channel(MANAGEMENT)
            await channel.send(embeds=[embedafter, embedbefore])
        elif before_role.name != after_role.name:
            embed = discord.Embed(title="Role Name Change ",
                                       description=f">>> **Role:** {after_role.mention}\n**New:** `@{after_role}`\n**Old:** `@{before_role}`",
                                       timestamp=discord.utils.utcnow(),
                                       color=after_role.color)
    @commands.Cog.listener("on_guild_channel_create")
    async def guild_channel_create_listener(self, channel:discord.abc.GuildChannel):
        if isinstance(channel, discord.CategoryChannel):
            embed = discord.Embed(title="Category Created",
                                description=f"A new category `{channel}` has been created.",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=1):
                if entry.target.id == channel.id:
                    mod = channel.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Created by @{mod}", icon_url=mod.display_avatar.url)
                    break
        else:
            embed = discord.Embed(title="Channel Created",
                                description=f"A new channel {channel.mention} has been created.",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_green())
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=1):
                if entry.target.id == channel.id:
                    mod = channel.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Created by @{mod}", icon_url=mod.display_avatar.url)
                    break
        channel = self.bot.get_channel(MANAGEMENT)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_channel_delete")
    async def guild_channel_delete_listener(self, channel:discord.abc.GuildChannel):
        if isinstance(channel, discord.CategoryChannel):
            embed = discord.Embed(title="Category Deleted",
                                description=f"The category `{channel}` has been deleted.",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                if entry.target.id == channel.id:
                    mod = channel.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Deleted by @{mod}", icon_url=mod.display_avatar.url)
                    break
        else:
            embed = discord.Embed(title="Channel Deleted",
                                description=f"The channel `#{channel.name}` has been deleted.",
                                timestamp=discord.utils.utcnow(),
                                color=discord.Color.brand_red())
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                if entry.target.id == channel.id:
                    mod = channel.guild.get_member(entry.user_id)
                    embed.set_footer(text=f"Deleted by @{mod}", icon_url=mod.display_avatar.url)
                    break
        channel = self.bot.get_channel(MANAGEMENT)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_channel_update")
    async def guild_channel_update_listener(self, before_channel:discord.abc.GuildChannel, after_channel:discord.abc.GuildChannel):
        if not isinstance(after_channel, discord.CategoryChannel):
            if before_channel.name != after_channel.name:
                embed = discord.Embed(title="Channel Name Change",
                                    description=f">>> **Channel:** {after_channel.mention} ({after_channel.id})\n**New:** `{after_channel.name}`\
                                        \n**Old:** `{before_channel.name}`",
                                        timestamp=discord.utils.utcnow(),
                                        color=discord.Color.blurple())
                async for entry in after_channel.guild.audit_logs(action=discord.AuditLogAction.channel_update, limit=1):
                    if entry.target.id == after_channel.id:
                        mod = after_channel.guild.get_member(entry.user_id)
                        embed.set_footer(text=f"Changed by @{mod}", icon_url=mod.display_avatar.url)
                        break
                channel = self.bot.get_channel(MANAGEMENT)
                await channel.send(embed=embed)
            elif before_channel.overwrites != after_channel.overwrites:
                after_channel_ovwerites = {}

                for role, perm_object in after_channel.overwrites.items():
                    allow, deny = perm_object.pair()
                    
                    allowed_perms = {perm for perm, value in allow if value}
                    denied_perms = {perm for perm, value in deny if value}

                    after_channel_ovwerites[role.name] = {
                        "allowed": allowed_perms,
                        "denied": denied_perms
                    }
                before_channel_overwrites = {}

                for role, perm_object in before_channel.overwrites.items():
                    allow, deny = perm_object.pair()
                    
                    allowed_perms = {perm for perm, value in allow if value}
                    denied_perms = {perm for perm, value in deny if value}

                    before_channel_overwrites[role.name] = {
                        "allowed": allowed_perms,
                        "denied": denied_perms
                    }
        else:
            if before_channel.name != after_channel.name:
                embed = discord.Embed(title="Category Name Change",
                                    description=f">>> **New:** `{after_channel.name}`\
                                        \n**Old:** `{before_channel.name}`",
                                        timestamp=discord.utils.utcnow(),
                                        color=discord.Color.blurple())
                async for entry in after_channel.guild.audit_logs(action=discord.AuditLogAction.channel_update, limit=1):
                    if entry.target.id == after_channel.id:
                        mod = after_channel.guild.get_member(entry.user_id)
                        embed.set_footer(text=f"Changed by @{mod}", icon_url=mod.display_avatar.url)
                        break
                channel = self.bot.get_channel(MANAGEMENT)
                await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_emojis_update")
    async def guild_emojis_update_listener(self, guild:discord.Guild, before:list[discord.Emoji], after: list[discord.Emoji]):
        if len(before) == len(after):
            emoji_change_list = [(old_emoji, new_emoji) for new_emoji in after for old_emoji in before if new_emoji.name != old_emoji.name and new_emoji.id == old_emoji.id]
            new_emoji :discord.Emoji = emoji_change_list[0][0]
            old_emoji :discord.Emoji = emoji_change_list[0][1]
            embed = discord.Embed(title="Emoji Name Updated",
                                  description=f">>> **New:** `{new_emoji.name}`\n**Old:** `{old_emoji.name}`",
                                  color=discord.Color.blurple(),
                                  timestamp=discord.utils.utcnow())
            async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_update, limit=1):
                if entry.target.id == emoji.id:
                    mod = guild.get_member(entry.user_id) or await guild.fetch_member(entry.user_id)
                    embed.set_footer(text=f"Updated by @{mod}", icon_url=mod.display_avatar.url)
            embed.set_thumbnail(url=new_emoji.url)
            channel = guild.get_channel(MOD_LOG)
            await channel.send(embed=embed)
        else:
            before_list = {emoji for emoji in before}
            after_list = {emoji for emoji in after}
            added = after_list - before_list
            removed = before_list - after_list
            if added:
                emoji : discord.Emoji = list(added)[0]
                embed = discord.Embed(title="Emoji Created",
                                    description=f">>> **Name:** `{emoji.name}`\n**Id:** {emoji.id}",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_green())
                embed.set_thumbnail(url=emoji.url)
                async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_create, limit=1):
                    if entry.target.id == emoji.id:
                        mod = guild.get_member(entry.user_id) or await guild.fetch_member(entry.user_id)
                        embed.set_footer(text=f"Created by @{mod}", icon_url=mod.display_avatar.url)
                channel = guild.get_channel(MOD_LOG)
                await channel.send(embed=embed)
            else:
                emoji : discord.Emoji = list(removed)[0]
                embed = discord.Embed(title="Emoji Deleted",
                                    description=f">>> **Name:** `{emoji.name}`\n**Id:** {emoji.id}\
                                        \n**Created:** <t:{int(emoji.created_at.timestamp())}:R>",
                                    timestamp=discord.utils.utcnow(),
                                    color=discord.Color.brand_red())
                embed.set_thumbnail(url=emoji.url)
                async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_delete, limit=1):
                    if entry.target.id == emoji.id:
                        mod = guild.get_member(entry.user_id) or await guild.fetch_member(entry.user_id)
                        embed.set_footer(text=f"Deleted by @{mod}", icon_url=mod.display_avatar.url)
                channel = guild.get_channel(MOD_LOG)
                await channel.send(embed=embed)
            
async def setup(bot:commands.Bot):
    await bot.add_cog(LogCogs(bot))
