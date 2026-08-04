import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_data):
        super().__init__(timeout=None)
        self.giveaway_data = giveaway_data

    @discord.ui.button(label="Çekilişe Katıl", style=discord.ButtonStyle.blurple, custom_id="join_giveaway_btn", emoji="🎉")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.giveaway_data["participants"]:
            self.giveaway_data["participants"].remove(user_id)
            await interaction.response.send_message("❌ Çekilişten katılımın kaldırıldı!", ephemeral=True)
        else:
            self.giveaway_data["participants"].add(user_id)
            await interaction.response.send_message("✅ Başarıyla çekilişe katıldın! Şansın bol olsun.", ephemeral=True)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="çekiliş", description="Sunucuda butonlu çekiliş başlatır.")
    @app_commands.describe(
        sure="Süre (Örn: 30s = 30 saniye, 5m = 5 dakika, 1h = 1 saat)",
        kazanan_sayisi="Kaç kişi kazanacak?",
        odul="Verilecek ödül nedir?"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, sure: str, kazanan_sayisi: int, odul: str):
        seconds = 0
        unit = sure[-1].lower()
        try:
            val = int(sure[:-1])
            if unit == 's':
                seconds = val
            elif unit == 'm':
                seconds = val * 60
            elif unit == 'h':
                seconds = val * 3600
            elif unit == 'd':
                seconds = val * 86400
            else:
                return await interaction.response.send_message("❌ Geçersiz süre formatı! Örnek: `30s`, `5m`, `2h`, `1d`", ephemeral=True)
        except ValueError:
            return await interaction.response.send_message("❌ Süre değerini hatalı girdin! Örnek: `10m`", ephemeral=True)

        giveaway_data = {
            "participants": set(),
            "host": interaction.user.id
        }

        embed = discord.Embed(
            title="🎉 ÇEKİLİŞ BAŞLADI! 🎉",
            description=f"**Ödül:** `{odul}`\n**Kazanan Sayısı:** `{kazanan_sayisi}`\n**Düzenleyen:** {interaction.user.mention}\n\n🎉 Katılmak için aşağıdaki **Çekilişe Katıl** butonuna bas!",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Süre: {sure}")

        view = GiveawayView(giveaway_data)
        await interaction.response.send_message("✅ Çekiliş başlatıldı!", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=view)

        await asyncio.sleep(seconds)

        participants = list(giveaway_data["participants"])
        
        ended_embed = discord.Embed(
            title="🎉 ÇEKİLİŞ SONUÇLANDI 🎉",
            description=f"**Ödül:** `{odul}`\n**Düzenleyen:** <@{giveaway_data['host']}>",
            color=discord.Color.dark_gold()
        )

        if len(participants) == 0:
            ended_embed.add_field(name="Kazananlar", value="Hiç kimse katılmadığı için kazanan olamadı! 😢")
        else:
            winners_count = min(kazanan_sayisi, len(participants))
            winners = random.sample(participants, winners_count)
            winner_mentions = ", ".join([f"<@{w}>" for w in winners])
            ended_embed.add_field(name="🏆 Kazanan(lar)", value=winner_mentions)
            await interaction.channel.send(f"Tebrikler {winner_mentions}! `{odul}` ödülünü kazandın! 🎉")

        for child in view.children:
            child.disabled = True
        
        await msg.edit(embed=ended_embed, view=view)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
