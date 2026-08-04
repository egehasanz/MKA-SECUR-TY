import discord
from discord.ext import commands
import re

# Küfür, Argo, AAT ve Reklam Listesi
FORBIDDEN_WORDS = [
    "aat",
    "amk", "aq", "aq.", "amina", "amina koyim", "amına", "orospu", "orospucocugu", 
    "piç", "pic", "sik", "sikik", "sikerim", "siktir", "yarrak", "yersen", 
    "göt", "götveren", "kahpe", "yavşak", "ibne", "oç", "o.ç.", "ananın", 
    "amq", "siktim", "siktiğimin", "pezevenk", "amcik", "amçık", "porno", "sikiş",
    "discord.gg/", "discord.com/invite/", "http://", "https://", "www."
]

AUTOMOD_LOG_CHANNEL_ID = 1534155785888600094  # Log kanalı ID'si
ROLES_TO_PING = [1515087391487168592]  # Etiketlenecek yetkili rol ID'leri

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Botları ve DM'leri yoksay
        if message.author.bot or not message.guild:
            return

        # Yöneticiler filtreden muaftır
        if message.author.guild_permissions.administrator:
            return

        content = message.content.lower()
        clean_content = re.sub(r'[^a-z0-9ğüşıöç]', '', content)
        
        triggered_word = None
        for word in FORBIDDEN_WORDS:
            clean_word = re.sub(r'[^a-z0-9ğüşıöç]', '', word)
            if word in content or (clean_word and clean_word in clean_content):
                triggered_word = word
                break

        if triggered_word:
            try:
                # 1. Mesajı anında sil
                await message.delete()

                # Roller için etiket metni oluştur
                role_mentions = " ".join([f"<@&{r_id}>" for r_id in ROLES_TO_PING])

                # 2. Kanala uyarı at (dahil ibaresi kaldırıldı) ve rolleri etiketle
                warning_msg = await message.channel.send(
                    f"⚠️ {message.author.mention}, yasaklı kelime, argo veya izinsiz içerik kullandığın için mesajın silindi! {role_mentions}"
                )
                await warning_msg.delete(delay=5)

                # 3. Log kanalına gönderilecek embed mesajı
                log_channel = message.guild.get_channel(AUTOMOD_LOG_CHANNEL_ID)
                if log_channel:
                    embed = discord.Embed(
                        title="🛡️ AutoMod Yasaklı İçerik Yakalandı",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Kullanıcı", value=f"{message.author} (`{message.author.id}`)", inline=False)
                    embed.add_field(name="Kanal", value=message.channel.mention, inline=False)
                    embed.add_field(name="Yakalanan Kelime", value=f"`{triggered_word}`", inline=False)
                    embed.add_field(name="Silinen Mesaj", value=f"```{message.content}```", inline=False)
                    embed.set_footer(text="AutoMod Sistemi")
                    
                    await log_channel.send(content=role_mentions, embed=embed)

            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"AutoMod Log Hatası: {e}")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
