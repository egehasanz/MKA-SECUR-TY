import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

GUILD_LOG_SETTINGS = {}
WARNINGS_DB = {}

OWNER_ID = 1507395734163689583  # Ege

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
        placeholder="Özel komutlar için yetki verilecek roller...",
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
        placeholder="Özel komutlar için yetki verilecek kişiler...",
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

    @app_commands.command(name="logsayar", description="Genel moderasyon ve sunucu loglarının gönderileceği kanalı ayarlar.")
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

    # --- KAPSAMLI LOG DİNLEYİCİLERİ ---

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(title="🗑️ Mesaj Silindi", color=discord.Color.red())
        embed.add_field(name="Kanal", value=message.channel.mention, inline=False)
        embed.add_field(name="Yazan", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Mesaj", value=message.content or "*İçerik yok (Görsel/Dosya olabilir)*", inline=False)
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        embed = discord.Embed(title="✏️ Mesaj Düzenlendi", color=discord.Color.orange())
        embed.add_field(name="Kanal", value=before.channel.mention, inline=False)
        embed.add_field(name="Kullanıcı", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Eski Hâli", value=before.content or "*Boş*", inline=False)
        embed.add_field(name="Yeni Hâli", value=after.content or "*Boş*", inline=False)
        await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = after.guild
        # İsim Değişikliği
        if before.nick != after.nick or before.name != after.name:
            embed = discord.Embed(title="👤 Kullanıcı Bilgisi Değişti", color=discord.Color.blue())
            embed.add_field(name="Kullanıcı", value=f"{after} ({after.id})", inline=False)
            embed.add_field(name="Eski İsim", value=f"{before.display_name}", inline=True)
            embed.add_field(name="Yeni İsim", value=f"{after.display_name}", inline=True)
            await self.send_log(guild, embed)

        # Rol Ekleme / Çıkarma
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles:
                embed = discord.Embed(title="➕ Kullanıcıya Rol Verildi", color=discord.Color.green())
                embed.add_field(name="Kullanıcı", value=f"{after.mention} ({after.id})", inline=False)
                embed.add_field(name="Verilen Rol(ler)", value=", ".join([r.name for r in added_roles]), inline=False)
                await self.send_log(guild, embed)

            if removed_roles:
                embed = discord.Embed(title="➖ Kullanıcıdan Rol Alındı", color=discord.Color.dark_red())
                embed.add_field(name="Kullanıcı", value=f"{after.mention} ({after.id})", inline=False)
                embed.add_field(name="Alınan Rol(ler)", value=", ".join([r.name for r in removed_roles]), inline=False)
                await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="📥 Sunucuya Katıldı", color=discord.Color.green())
        embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="📤 Sunucudan Ayrıldı", color=discord.Color.red())
        embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title="📁 Kanal Oluşturuldu", color=discord.Color.green())
        embed.add_field(name="Kanal Adı", value=channel.name, inline=False)
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title="🗑️ Kanal Silindi", color=discord.Color.red())
        embed.add_field(name="Kanal Adı", value=channel.name, inline=False)
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.overwrites != after.overwrites:
            embed = discord.Embed(title="🔒 Kanal İzinleri Değiştirildi", color=discord.Color.orange())
            embed.add_field(name="Kanal", value=after.mention, inline=False)
            await self.send_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        guild = member.guild
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(title="🔊 Ses Kanalına Katıldı", color=discord.Color.purple())
            embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Kanal", value=after.channel.name, inline=False)
            await self.send_log(guild, embed)
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(title="🔇 Ses Kanalından Ayrıldı", color=discord.Color.dark_purple())
            embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Kanal", value=before.channel.name, inline=False)
            await self.send_log(guild, embed)
        elif before.channel != after.channel and before.channel is not None and after.channel is not None:
            embed = discord.Embed(title="🔀 Ses Kanalı Değiştirdi", color=discord.Color.blue())
            embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Eski Kanal", value=before.channel.name, inline=True)
            embed.add_field(name="Yeni Kanal", value=after.channel.name, inline=True)
            await self.send_log(guild, embed)

    # --- MODERASYON KOMUTLARI ---

    @app_commands.command(name="temizle", description="Kanaldaki mesajları belirtilen miktarda veya tamamen temizler.")
    @app_commands.describe(miktar="Silinecek mesaj sayısı (1-100 arası) veya 'all' yazarak tamamını sil")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def temizle(self, interaction: discord.Interaction, miktar: str):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel

        if miktar.lower() == "all":
            deleted_count = 0
            while True:
                deleted = await channel.purge(limit=100)
                if not deleted:
                    break
                deleted_count += len(deleted)
            await interaction.followup.send(f"🧹 Kanal tamamen temizlendi! Toplam **{deleted_count}** mesaj silindi.", ephemeral=True)
        else:
            try:
                limit_val = int(miktar)
                if limit_val < 1 or limit_val > 100:
                    return await interaction.followup.send("❌ Lütfen 1 ile 100 arasında bir sayı girin veya 'all' yazın.", ephemeral=True)
                
                deleted = await channel.purge(limit=limit_val)
                await interaction.followup.send(f"🧹 Başarıyla **{len(deleted)}** mesaj silindi.", ephemeral=True)
            except ValueError:
                await interaction.followup.send("❌ Geçersiz değer! Sayı girmeli veya 'all' yazmalısın.", ephemeral=True)

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
            embed = discord.Embed(title="Bot Bilgilendirme Mesajı", description=mesaj, color=discord.Color.blue())
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
        if member.id == OWNER_ID:
            return await ctx.send("❌ Geliştiricime (Ege) bu işlemi yapamam!", delete_after=5)
        
        guild_id = ctx.guild.id
        if guild_id not in WARNINGS_DB:
            WARNINGS_DB[guild_id] = {}
        if member.id not in WARNINGS_DB[guild_id]:
            WARNINGS_DB[guild_id][member.id] = []
        
        WARNINGS_DB[guild_id][member.id].append({"sebep": sebep, "yetkili": str(ctx.author)})
        
        await ctx.send(f"⚠️ **{member.display_name}** adlı kullanıcı uyarıldı. **Sebep:** {sebep}")
        
        embed = discord.Embed(title="Kullanıcı Uyarıldı", color=discord.Color.yellow())
        embed.add_field(name="Kullanıcı", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Yetkili", value=ctx.author.mention, inline=False)
        embed.add_field(name="Sebep", value=sebep, inline=False)
        await self.send_log(ctx.guild, embed)

    @commands.command(name="uyarilar")
    @commands.has_permissions(kick_members=True)
    async def uyarilar(self, ctx, member: discord.Member):
        await ctx.message.delete()
        guild_id = ctx.guild.id
        user_warnings = WARNINGS_DB.get(guild_id, {}).get(member.id, [])
        
        if not user_warnings:
            return await ctx.send(f"✅ **{member.display_name}** adlı kullanıcısının hiç uyarısı yok.", delete_after=10)
        
        embed = discord.Embed(title=f"⚠️ {member.display_name} - Uyarı Geçmişi", color=discord.Color.gold())
        for i, warn in enumerate(user_warnings, 1):
            embed.add_field(name=f"Uyarı #{i}", value=f"**Sebep:** {warn['sebep']}\n**Yetkili:** {warn['yetkili']}", inline=False)
        
        await ctx.send(embed=embed, delete_after=20)

    @commands.command(name="sustur")
    @commands.has_permissions(moderate_members=True)
    async def sustur(self, ctx, member: discord.Member, dakika: int, *, sebep: str = "Sebep belirtilmedi"):
        await ctx.message.delete()
        if member.id == OWNER_ID:
            return await ctx.send("❌ Geliştiricime (Ege) bu işlemi yapamam!", delete_after=5)
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
        if member.id == OWNER_ID:
            return await ctx.send("❌ Geliştiricime (Ege) bu işlemi yapamam!", delete_after=5)
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
        if member.id == OWNER_ID:
            return await ctx.send("❌ Geliştiricime (Ege) bu işlemi yapamam!", delete_after=5)
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

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, sebep: str = "Sebep belirtilmedi"):
        await ctx.message.delete()
        if user_id == OWNER_ID:
            return await ctx.send("❌ Geliştiricime (Ege) bu işlemi yapamam!", delete_after=5)
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=sebep)
            await ctx.send(f"✅ **{user.display_name}** adlı kullanıcının banı kaldırıldı.", delete_after=10)
            
            embed = discord.Embed(title="Kullanıcının Banı Kaldırıldı (Unban)", color=discord.Color.green())
            embed.add_field(name="Kullanıcı", value=f"{user} ({user.id})", inline=False)
            embed.add_field(name="Yetkili", value=ctx.author.mention, inline=False)
            embed.add_field(name="Sebep", value=sebep, inline=False)
            await self.send_log(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"Unban başarısız: {e}", delete_after=5)

    @commands.command(name="bansorgu")
    @commands.has_permissions(ban_members=True)
    async def bansorgu(self, ctx, user_id: int):
        await ctx.message.delete()
        try:
            ban_entry = await ctx.guild.fetch_ban(discord.Object(id=user_id))
            embed = discord.Embed(title="🔍 Ban Sorgulama Sonucu", color=discord.Color.blue())
            embed.add_field(name="Kullanıcı", value=f"{ban_entry.user} ({ban_entry.user.id})", inline=False)
            embed.add_field(name="Yasaklama Sebebi", value=ban_entry.reason or "Sebep belirtilmemiş", inline=False)
            await ctx.send(embed=embed, delete_after=15)
        except discord.NotFound:
            await ctx.send("❌ Bu ID'ye sahip yasaklı bir kullanıcı bulunamadı.", delete_after=5)
        except Exception as e:
            await ctx.send(f"Sorgulama sırasında hata oluştu: {e}", delete_after=5)

    @app_commands.command(name="help", description="Botun düzenlenmiş kapsamlı komut listesini gösterir.")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📖 MKA Bot Kapsamlı Yardım Menüsü", color=discord.Color.blurple())
        
        embed.add_field(
            name="👑 Bot Sahibi & Yetkilendirilmiş Komutlar", 
            value="`.dm @kullanıcı [mesaj]` - Özel DM gönderir *(Bot Sahibi veya /ownerpanel yetkilileri)*", 
            inline=False
        )
        
        embed.add_field(
            name="🛡️ Moderasyon Komutları (Yetkili Gerekir)", 
            value=(
                "`.uyar @kullanıcı [sebep]` - Kullanıcıyı uyarır\n"
                "`.uyarilar @kullanıcı` - Kullanıcının uyarı geçmişini gösterir\n"
                "`.sustur @kullanıcı [dakika] [sebep]` - Kullanıcıya timeout atar\n"
                "`.kick @kullanıcı [sebep]` - Sunucudan atar\n"
                "`.ban @kullanıcı [sebep]` - Sunucudan yasaklar\n"
                "`.unban [kullanıcı_id] [sebep]` - Ban kaldırır\n"
                "`.bansorgu [kullanıcı_id]` - Ban durumunu sorgular\n"
                "`.kilit` - Kanalı mesajlara kapatır\n"
                "`.aç` - Kanalı mesajlara açar"
            ), 
            inline=False
        )

        embed.add_field(
            name="⚙️ Slash (/) Komutları", 
            value=(
                "`/help` - Yardım menüsünü açar\n"
                "`/ownerpanel` - Bot sahibi yetki yönetim paneli **(Sadece Owner)**\n"
                "`/ticket` - Destek paneli gönderir *(Admin)*\n"
                "`/temizle [sayı / all]` - Mesajları temizler *(Mesaj Yönetimi)*\n"
                "`/logsayar #kanal` - Moderasyon/Sunucu log ayarlar *(Admin)*\n"
                "`/ticketlogsayar #kanal` - Transkript log ayarlar *(Admin)*"
            ), 
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
