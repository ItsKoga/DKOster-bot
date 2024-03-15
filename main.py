import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

import log_helper

# Load environment variables
load_dotenv()

# Create bot instance
bot = commands.Bot(intents = discord.Intents.all())

#create logger
log = log_helper.create("Main")

# Event for when the bot is ready
@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Game(name = "Oster event"), status = discord.Status.online)
    log("Bot ist Online!", "SUCCESS")


# Load all cogs
log("Lade Cogs...", "SYSTEM")
if __name__ == "__main__":
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            log(f"{filename} wird geladen!")
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                log(f"Beim Laden von {filename} ist ein Fehler aufgetreten: {e}", "CRITICAL")
    log("Alle Cogs wurden geladen!", "SUCCESS")

    # Run the bot
    log("Starte Bot...", "SYSTEM")
    bot.run(os.getenv('TOKEN'))