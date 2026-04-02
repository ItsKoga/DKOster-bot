import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

import system
import log_helper

load_dotenv()
log = log_helper.create("Main")


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.db: system.SQLiteCacheDB | None = None


bot = MyBot()


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Oster event"), status=discord.Status.online)
    log("Bot ist Online!", "SUCCESS")


async def main():
    # 1) DB starten (VOR bot.start / also bevor der Bot online geht)
    log("Initialisiere Database-Handler (SQLite + Cache)...", "SYSTEM")
    bot.db = system.SQLiteCacheDB(bot, db_path="data.db")
    await bot.db.start()
    system.Database.set_handler(bot.db)
    log("Database-Handler gestartet & Cache geladen.", "SUCCESS")

    # 2) Cogs laden (VOR connect/login)
    log("Lade Cogs...", "SYSTEM")
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            log(f"{filename} wird geladen!")
            try:
                # Viele py-cord Versionen: load_extension ist async
                bot.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                log(f"Beim Laden von {filename} ist ein Fehler aufgetreten: {e}", "CRITICAL")
    log("Alle Cogs wurden geladen!", "SUCCESS")

    # 3) Bot starten (ersetzt bot.run)
    token = os.getenv("TOKEN")
    log("Starte Bot...", "SYSTEM")
    log(f"Token loaded: {bool(token)}", "DEBUG")

    try:
        await bot.start(token)
    finally:
        # garantiertes Shutdown-Cleanup (CTRL+C, Crash, etc.)
        if bot.db:
            log("Shutdown: Flush + DB close...", "SYSTEM")
            await bot.db.close()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())