import discord
from discord.ext import commands
from discord import app_commands
import io

GUILD_TICKET_LOGS = {}

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Bileti Kapat", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        channel = interaction.channel
        guild = interaction.guild

        messages = [message async for message in channel.history(limit=None, oldest_first=True)]
        
        # Hatanın düzeldiği satır burada:
        transcript_content = f"--- TICKET TRANSKRİPTİ: {channel.name} ---\n\n"
        
        for msg in messages:
            transcript_content += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author}: {msg.content}\n"

        file = discord.File(io.BytesIO(transcript_content.encode('utf-8')), filename=f"{channel.name}-transkript.txt")

        log_channel_id = GUILD_TICKET_LOGS.get(guild.id)
        if log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title="Bilet Kapatıldı ve Transkript Alındı", color=discord.Color.blue())
                embed.add_field(name="Kanal Adı", value=channel.name, inline=False)
                embed.add_field(name="Kapatan Yetkili", value=interaction.user.mention, inline=False)
                await log_channel.send(embed=embed, file=file)

        await interaction.followup.send("Bilet başarıyla kapatılıyor...", ephemeral=True)
        await channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticketlogsayar", description="Ticket transkriptlerinin gönderileceği kanalı ayarlar.")
    @app_commands.describe(kanal="Transkriptlerin iletileceği metin kanalı")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_log_ayar(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        GUILD_TICKET_LOGS[interaction.guild.id] = kanal.id
        await interaction.response.send_message(f"✅ Başarılı! Ticket transkript kanalı {kanal.mention} olarak ayarlandı.", ephemeral=True)

    @app_commands.command(name="ticket", description="Yeni bir destek talebi (ticket) oluşturur.")
    async def ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        category_name = "Destek Talepleri"
        
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        channel_name = f"ticket-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            return await interaction.response.send_message(f"Zaten açık bir destek kanalın var: {existing_channel.mention}", ephemeral=True)

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="Destek Talebi Oluşturuldu",
            description="Yetkililer en kısa sürede sizinle ilgilenecektir.\nTalebi sonlandırmak için aşağıdaki butonu kullanabilirsiniz.",
            color=discord.Color.green()
        )

        await ticket_channel.send(content=f"{interaction.user.mention} Hoş geldin!", embed=embed, view=TicketView())
        await interaction.response.send_message(f"Destek kanalınız oluşturuldu: {ticket_channel.mention}", ephemeral=True)

    @app_commands.command(name="help", description="Botun komut listesini gösterir.")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📖 Python Bot Yardım Menüsü", color=discord.Color.blurple())
        embed.add_field(name="Prefix Komutları (`.`)", value="`.uyar @kullanici [sebep]`\n`.sustur @kullanici [dakika] [sebep]`\n`.kick @kullanici [sebep]`\n`.ban @kullanici [sebep]`\n`.dm @kullanici [mesaj]` (Sadece Owner)", inline=False)
        embed.add_field(name="Slash Komutları (`/`)", value="`/help` - Yardım menüsü\n`/ticket` - Destek talebi açar\n`/ownerpanel` - Yetki paneli\n`/logsayar #kanal` - Moderasyon log\n`/ticketlogsayar #kanal` - Transkript log", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
