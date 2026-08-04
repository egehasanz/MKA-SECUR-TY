import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

GUILD_LOG_SETTINGS = {}
OWNER_ID = int(os.getenv("OWNERİD", 0))

AUTHORIZED_USERS = {}  
AUTHORIZED_ROLES = {}  

def is_owner_or_authorized():
    async def predicate(ctx):
        if ctx.author.id == OWNER_ID:
            return True
        guild_id = ctx.guild.id
        if ctx.author.id in AUTHORIZED_USERS.get(guild_id, set()):
            return True
        user_roles = [role.id for role in ctx.author.roles]
        if any(role_id in AUTHORIZED_ROLES.get(guild_id, set()) for role_id in user_roles):
            return True
        return False
    return commands.check(predicate)

class OwnerPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Yetki verilecek rolleri seç...",
        min_values=0,
        max_values=5,
        custom_id="select_roles"
    )
    async def select_roles(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("Bu paneli sadece bot sahibi kullanabilir!", ephemeral=True)
        
        guild_id = interaction.guild.id
        if guild_id not in AUTHORIZED_ROLES:
            AUTHORIZED_ROLES[guild_id] = set()
        
        selected_role_ids = [role.id for role in select.values]
        AUTHORIZED_ROLES[guild_id] = set(selected_role_ids)
        
        roles_str = ", ".join([role.mention for role in select.values]) if select.values else "Hiçbiri"
        await interaction.response.send_message(f"✅ Yetkili roller güncellendi: {roles_str}", ephemeral=True)

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Yetki verilecek kişileri seç...",
        min_values=0,
        max_values=5,
        custom_id="select_users"
    )
    async def select_users(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("Bu paneli sadece bot sahibi kullanabilir!", ephemeral=True)
        
        guild_id = interaction.guild.id
        if guild_id not in AUTHORIZED_USERS:
            AUTHORIZED_USERS[guild_id] = set()
        
        selected_user_ids = [user.id for user in select.values]
        AUTHORIZED_USERS[guild_id] = set(selected_user_ids)
        
        users_str = ", ".join([user.mention for user in select.values]) if select.values else "Hiçbiri"
        await interaction.response.send_message(f"✅ Yetkili kişiler güncellendi: {users_str}", ephemeral=True)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ownerpanel", description="Bot sahibine özel yetki yönetim panelini açar.")
    async def owner_panel(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("Bu komutu yalnızca botun sahibi kullanabilir.", ephemeral=True)

        embed = discord.Embed(
            title="👑 Bot Yetki Yönetim Paneli",
            description="Aşağıdaki menüleri kullanarak bot üzerindeki özel komutlara (örneğin `.dm`) erişebilecek **rolleri** ve **kişileri** seçebilirsin.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=OwnerPanelView(), ephemeral=True)

    @app_commands.command(name="logsayar", description="Genel moderasyon loglarının gönderileceği kanalı ayarlar.")
    @app_commands.describe(kanal="Logların gönderileceği metin kanalı")
    @app_commands.checks.has_permissions(administrator=True)
    async def log_ayar(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        GUILD_LOG_SETTINGS[interaction.guild.id] = kanal.id
        await interaction.response.send_message(f"✅ Başarılı! Log kanalı {kanal.mention} olarak ayarlandı.", ephemeral=True)

    async def send_log(self, guild, embed):
        channel_id = GUILD_LOG_SETTINGS.get(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    @commands.command(name="kilit")
    @commands.has_permissions(manage_channels=True)
    async def kilit(self, ctx):
        await ctx.message.delete()
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send("🔒 Bu kanal **kilitlendi**.", delete_after=10)
        except Exception as e:
            await ctx.send(f"Kanal kilitlenirken bir hata oluştu: {e}", delete_after=5)

    @commands.command(name="aç")
    @commands.has_permissions(manage_channels=True)
    async def ac(self, ctx):
        await ctx.message.delete()
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send("🔓 Bu kanalın kilidi **açıldı**.", delete_after=10)
        except Exception as e:
            await ctx.send(f"Kanalın kilidi açılırken bir hata oluştu: {e}", delete_after=5)

    @commands.command(name="dm")
    @is_owner_or_authorized()
    async def dm(self, ctx, member: discord.Member, *, mesaj: str):
        await ctx.message.delete()

        try:
            embed = discord.Embed(
                title="Bot Bilgilendirme Mesajı",
                description=mesaj,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"{ctx.guild.name} sunucusundan gönderildi.")
            
            await member.send(embed=embed)
            await ctx.send(f"✅ **{member.display_name}** adlı kullanıcıya DM başarıyla gönderildi.", delete_after=5)
        except discord.Forbidden:
            await ctx.send(f"❌ **{member.display_name}** adlı kullanıcının DM kutusu kapalı olduğu için mesaj gönderilemedi.", delete_after=5)
        except Exception as e:
            await ctx.send(f"DM gönderilirken bir hata oluştu: {e}", delete_after=5)

    @commands.command(name="uyar")
    @commands.has_permissions(kick_members=True)
    async def uyar(self, ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi"):
        await ctx.message.delete()
        await ctx.send(f"⚠️ **{member.display_name}** adlı kullanıcı uyarıldı. **Sebep:** {sebep}")
        
        embed = discord.Embed(title="Kullanıcı Uyarıldı", color=discord.Color.yellow())
        embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Yetkili", value=ctx.author.mention, inline=False)
        embed.add_field(name="Sebep", value=sebep, inline=False)
        await self.send_log(ctx.guild, embed)

    @commands.command(name="sustur")
    @commands.has_permissions(moderate_members=True)
    async def sustur(self, ctx, member: discord.Member, dakika: int, *, sebep: str = "Sebep belirtilmedi"):
        await ctx.message.delete()
        try:
            duration = timedelta(minutes=dakika)
            await member.timeout(duration, reason=sebep)
            await ctx.send(f"🔇 **{member.display_name}** {dakika} dakika süreyle susturuldu. **Sebep:** {sebep}")
            
            embed = discord.Embed(title="Kullanıcı Susturuldu (Timeout)", color=discord.Color.orange())
            embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Süre", value=f"{dakika} dakika", inline=False)
            embed.add_field(name="Yetkili", value=ctx.author.mention, inline=False)
            embed.add_field(name="Sebep", value=sebep, inline=False)
            await self.send_log(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"Susturma başarısız: {e}")

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi"):
        await ctx.message.delete()
        try:
            await member.kick(reason=sebep)
            await ctx.send(f"👢 **{member.display_name}** sunucudan atıldı. **Sebep:** {sebep}")
            
            embed = discord.Embed(title="Kullanıcı Sunucudan Atıldı (Kick)", color=discord.Color.red())
            embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Yetkili", value=ctx.author.mention, inline=False)
            embed.add_field(name="Sebep", value=sebep, inline=False)
            await self.send_log(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"Atma işlemi başarısız: {e}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi"):
        await ctx.message.delete()
        try:
            await member.ban(reason=sebep)
            await ctx.send(f"🔨 **{member.display_name}** sunucudan yasaklandı. **Sebep:** {sebep}")
            
            embed = discord.Embed(title="Kullanıcı Yasaklandı (Ban)", color=discord.Color.dark_red())
            embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Yetkili", value=ctx.author.mention, inline=False)
            embed.add_field(name="Sebep", value=sebep, inline=False)
            await self.send_log(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"Yasaklama başarısız: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
