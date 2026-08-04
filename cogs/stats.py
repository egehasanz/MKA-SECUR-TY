import discord
from discord.ext import commands

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_guild_stats(self, guild: discord.Guild):
        try:
            total_members = guild.member_count
            bot_count = sum(1 for m in guild.members if m.bot)
            human_count = total_members - bot_count
            online_count = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)

            for channel in guild.voice_channels:
                name = channel.name.lower()
                new_name = None
                
                if "toplam üye" in name:
                    new_name = f"👥 Toplam Üye: {total_members}"
                elif "aktif üye" in name:
                    new_name = f"🟢 Aktif Üye: {online_count}"
                elif name.strip() == "bot" or ("bot" in name and "toplam" not in name):
                    new_name = f"🤖 Bot: {bot_count}"
                elif name.strip() == "üye" or name.strip() == "👤 üye":
                    new_name = f"👤 Üye: {human_count}"

                # Sadece isim farklıysa ve rate limit yememek için dikkatlice güncelle
                if new_name and channel.name != new_name:
                    await channel.edit(name=new_name)
        except discord.HTTPException as e:
            if e.status == 429:
                print("⚠️ Discord rate limit uyguladı, sayaç güncellemesi bir sonraki üye hareketine ertelendi.")
            else:
                print(f"Sayaç HTTP Hatası: {e}")
        except Exception as e:
            print(f"Sayaç güncelleme hatası: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.update_guild_stats(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.update_guild_stats(member.guild)

    @commands.Cog.listener()
    async def on_ready(self):
        # Bot ilk açıldığında sunucuları bir kere günceller
        for guild in self.bot.guilds:
            await self.update_guild_stats(guild)

async def setup(bot):
    await bot.add_cog(Stats(bot))
