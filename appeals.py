import discord
class FeedbackModal(discord.ui.Modal, title="Meowderator Form"):
    name = discord.ui.TextInput(label="Your Name", placeholder="John Doe", required=True)
    whywanna = discord.ui.TextInput(label="Why you wanna appeal for this?", style=discord.TextStyle.paragraph, required=True)
    security = discord.ui.TextInput(label="Do you have 2FA enabled?", placeholder="Yes", required=True)

    async def on_submit(self,  interaction: discord.Interaction):
        await interaction.response.send_message(f"Thanks, **{self.name}**, for opening a thread! Please wait...", ephemeral=True, delete_after=5)
        thread = await interaction.channel.create_thread(name=f"Mod Appeal - {interaction.user.name}", type=discord.ChannelType.private_thread, auto_archive_duration=60)
        embed = discord.Embed(title="Meowderator Application", color=discord.Color.blue())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.add_field(name="Name", value=self.name.value, inline=False)
        embed.add_field(name="Reason for Appeal", value=self.whywanna.value, inline=False)
        embed.add_field(name="2FA Enabled?", value=self.security.value, inline=False)
        embed.set_footer(text="Mod Application Thread")
        await thread.send(embed=embed)
        await thread.send("thanks for applying! Moderators will review your application below.")

class FeedbackButton(discord.ui.View):
    @discord.ui.button(label="Meowderator Form", style=discord.ButtonStyle.primary, custom_id="meow_form_button")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FeedbackModal())
