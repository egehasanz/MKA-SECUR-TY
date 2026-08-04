import discord
from discord.ext import commands
import re

# Küfür, Argo, AAT ve Reklam Listesi
FORBIDDEN_WORDS = [
    "aat",
    "amk", "aq", "aq.", "amina", "amina koyim", "amına", "orospu", "orospucocugu", 
    "piç", "pic", "sik", "sikik", "sikerim", "siktir", "yarrak", "yersen", 
    "göt", "götveren", "kahpe", "yavşak", "ibne", "oç", "o.ç.", "ananın", 
    "amq", "siktim", "siktiğimin", "pezevenk", "amcik", "amçık",
    "discord.gg/", "discord.com/invite/", "http://", "https://", "www."
]

AUTOMOD_LOG_CHANNEL_ID = 1534155785888600094  # Log kanalı ID'si
ROLE_TO_PING_ID = 1515087391487168592         # Etiketlenecek rol ID'si

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
        
        # Kelimeler arası boşlukları ve yabancı karakterleri sadeleştirerek arama yap
        # Örn: "a a t", "a-a-t" gibi kaçışları da yakalamak için
        clean_content = re.sub(r'[^a-z0-9ğüşıöç]', '', content)
        
        triggered_word = None
        for word in FORBIDDEN_WORDS:
            # Hem normal metin içinde hem de sadeleştirilmiş metinde arar
            clean_word = re.sub(r'[^a-z0-9ğüşıöç]', '', word)
            if word in content or (clean_word and clean_word in clean_content):
                triggered_word = word
                break

        if triggered_word:
            try:
                # 1. Mesajı anında sil
                await message.delete()

                # 2. Kanala geçici uyarı at ve belirtilen ID'yi etiketle
                warning_msg = await message.channel.send(
                    f"⚠️ {message.author.mention}, bu sunucuda yasaklı kelime veya argo içerik (**{triggered_word}** dahil) kullanmak yasaktır! "
                    f"(<@&{ROLE_TO_PING_ID}>)"
                )
                await warning_msg.delete(delay=5)

                # 3. Belirttiğin AutoMod log kanalına log gönder
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
                    embed.set_footer(text=f"AutoMod Sistemi • Yetkili Etiketi: <@&{ROLE_TO_PING_ID}>")
                    
                    await log_channel.send(embed=embed)

            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"AutoMod Log Hatası: {e}")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
