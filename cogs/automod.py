import discord
from discord.ext import commands
from discord import app_commands

# Kapsamlı Küfür, Argo, AAT ve Reklam Filtresi Listesi
FORBIDDEN_WORDS = [
    # Senin özellikle istediğin kalıp
    "aat",
    
    # Küfür ve Argo Kalıpları
    "amk", "aq", "aq.", "amina", "amina koyim", "amına", "orospu", "orospucocugu", 
    "piç", "pic", "sik", "sikik", "sikerim", "siktir", "yarrak", "yersen", 
    "göt", "götveren", "kahpe", "yavşak", "ibne", "oç", "o.ç.", "ananın", 
    "amq", "siktim", "siktiğimin", "pezevenk", "amcik", "amçık",
    
    # Reklam ve Zararlı Bağlantı Kalıpları
    "discord.gg/", "discord.com/invite/", "http://", "https://", "www."
]

# Belirttiğin Özel ID'ler
AUTOMOD_LOG_CHANNEL_ID = 1534155785888600094  # Logların atılacağı kanal ID'si
ROLE_TO_PING_ID = 1515087391487168592         # Yasaklı kelimede etiketlenecek rol/kullanıcı ID'si

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Botların mesajlarını ve DM'leri yoksay
        if message.author.bot or not message.guild:
            return

        # Yönetici yetkisine sahip olanlar filtreden muaftır
        if message.author.guild_permissions.administrator:
            return

        content_lower = message.content.lower()
        triggered_word = None

        # Yasaklı kelime / reklam kontrolü
        for word in FORBIDDEN_WORDS:
            if word in content_lower:
                triggered_word = word
                break

        if triggered_word:
            try:
                # 1. Kullanıcının mesajını anında sil
                await message.delete()

                # 2. Kanala uyarı mesajı gönder (Belirttiğin ID'yi etiketleyerek)
                warning_msg = await message.channel.send(
                    f"⚠️ {message.author.mention}, bu sunucuda yasaklı kelime, argo veya izinsiz içerik (AAT dahil) paylaşmak yasaktır! "
                    f"Yetkililer bilgilendirildi. (<@&{ROLE_TO_PING_ID}>)"
                )
                await warning_msg.delete(delay=5) # 5 saniye sonra uyarı mesajını temizler

                # 3. Belirttiğin AutoMod log kanalına detaylı embed gönder
                log_channel = message.guild.get_channel(AUTOMOD_LOG_CHANNEL_ID)
                if log_channel:
                    embed = discord.Embed(
                        title="🛡️ AutoMod Yasaklı İçerik Yakalandı",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Kullanıcı", value=f"{message.author} (`{message.author.id}`)", inline=False)
                    embed.add_field(name="Kanal", value=message.channel.mention, inline=False)
                    embed.add_field(name="Yakalanan Kelime/İçerik", value=f"`{triggered_word}`", inline=False)
                    embed.add_field(name="Silinen Mesaj İçeriği", value=f"```{message.content}```", inline=False)
                    embed.set_footer(text=f"AutoMod Sistemi • İlgili Yetkili Etiketi: <@&{ROLE_TO_PING_ID}>")
                    
                    await log_channel.send(embed=embed)

            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"AutoMod hata oluştu: {e}")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
