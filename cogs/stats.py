import discord
from discord.ext import commands, tasks

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.update_stats.is_running():
            self.update_stats.start()

    @tasks.loop(minutes=15)
    async def update_stats(self):
        for guild in self.bot.guilds:
            try:
                total_members = guild.member_count
                bot_count = sum(1 for m in guild.members if m.bot)
                human_count = total_members - bot_count
                online_count = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)

                # Kanalları tek tek kontrol ederek tam eşleşme ile güncelle
                for channel in guild.voice_channels:
                    name = channel.name.lower()
                    
                    if "toplam üye" in name:
                        await channel.edit(name=f"👥 Toplam Üye: {total_members}")
                    elif "aktif üye" in name:
                        await channel.edit(name=f"🟢 Aktif Üye: {online_count}")
                    elif "bot:" in name or name.startswith("bot"):
                        await channel.edit(name=f"🤖 Bot: {bot_count}")
                    elif name.startswith("👤 üye") or name == "👤 üye":
                        await channel.edit(name=f"👤 Üye: {human_count}")
            except Exception as e:
                print(f"Sayaç güncelleme hatası ({guild.name}): {e}")

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Stats(bot))
