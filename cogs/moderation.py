import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

GUILD_LOG_SETTINGS = {}
OWNER_ID = int(os.getenv("OWNERİD", 0))

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.command(name="dm")
    async def dm(self, ctx, member: discord.Member, *, mesaj: str):
        await ctx.message.delete()
        
        if ctx.author.id != OWNER_ID:
            return await ctx.send("Bu komutu yalnızca botun sahibi kullanabilir.", delete_after=5)

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
