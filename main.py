import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOTTOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} olarak giriş yapıldı!")
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.giveaway")
    await bot.load_extension("cogs.tickets")
    await bot.load_extension("cogs.stats")
    await bot.load_extension("cogs.automod")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} adet slash komutu senkronize edildi.")
    except Exception as e:
        print(e)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Bu komutu kullanmak için gerekli yetkiye sahip değilsin.", delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"Bir hata oluştu: {error}")

if __name__ == "__main__":
    bot.run(TOKEN)
