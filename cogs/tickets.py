import discord
from discord.ext import commands
from discord import app_commands
import io

GUILD_TICKET_LOGS = {}
ROLE_IDS_TO_PING = [1515087391487168592, 1515134844643053580]

class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Oluştur", style=discord.ButtonStyle.success, custom_id="create_ticket_btn", emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild
        category_name = "Destek Talepleri"
        
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        # Temel izinler (Herkese kapalı)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        # Belirttiğin rol ID'lerine kanalı görme ve yazma izni otomatik ekleniyor
        for role_id in ROLE_IDS_TO_PING:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel_name = f"ticket-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            return await interaction.followup.send(f"Zaten açık bir destek kanalın var: {existing_channel.mention}", ephemeral=True)

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

        roles_mention = " ".join([f"<@&{role_id}>" for role_id in ROLE_IDS_TO_PING])
        ping_content = f"{interaction.user.mention} Hoş geldin! {roles_mention}"

        await ticket_channel.send(content=ping_content, embed=embed, view=TicketCloseView())
        await interaction.followup.send(f"Destek kanalınız oluşturuldu: {ticket_channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Bileti Kapat", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Bu bileti yalnızca yetkililer kapatabilir!", ephemeral=True)

        await interaction.response.defer(thinking=True, ephemeral=True)
        channel = interaction.channel
        guild = interaction.guild

        messages = [message async for message in channel.history(limit=None, oldest_first=True)]
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

    @app_commands.command(name="ticket", description="Destek talebi oluşturma panelini gönderir.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Destek Sistemi",
            description="Sunucumuzda bir sorun yaşarsanız veya yardıma ihtiyacınız olursa aşağıdaki **Destek Talebi Oluştur** butonuna tıklayarak özel kanal açabilirsiniz.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Destek Ekibi")
        await interaction.channel.send(embed=embed, view=TicketCreateView())
        await interaction.response.send_message("✅ Ticket paneli bu kanala başarıyla gönderildi.", ephemeral=True)

    @app_commands.command(name="help", description="Botun komut listesini gösterir.")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📖 Python Bot Yardım Menüsü", color=discord.Color.blurple())
        embed.add_field(name="Prefix Komutları (`.`)", value="`.uyar` | `.sustur` | `.kick` | `.ban` | `.kilit` | `.aç` | `.dm` (Sadece Owner)", inline=False)
        embed.add_field(name="Slash Komutları (`/`)", value="`/help` - Yardım menüsü\n`/ticket` - Ticket paneli gönderir (Admin)\n`/ownerpanel` - Yetki paneli\n`/logsayar #kanal` - Moderasyon log\n`/ticketlogsayar #kanal` - Transkript log", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
