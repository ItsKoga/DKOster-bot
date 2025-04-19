import discord
from discord.ext import commands

import os
from dotenv import load_dotenv
import system

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

# Create all required tables if they don't exist
system.Database.execute_and_commit("""
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(20) PRIMARY KEY,
    last_hit BIGINT DEFAULT 0,
    egg_talisman INT DEFAULT 0,
    rabbit_foot_count INT DEFAULT 0,
    used_rabbit_foot_count INT DEFAULT 0,
    notifications BOOLEAN DEFAULT TRUE,
    points INT DEFAULT 0,
    last_fight BIGINT DEFAULT 0,
    used_collect INT DEFAULT 0,
    found_nests INT DEFAULT 0,
    tickets INT DEFAULT 0
)""")

system.Database.execute_and_commit("""
CREATE TABLE IF NOT EXISTS eggs (
    egg_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id VARCHAR(20),
    creator_id VARCHAR(20),
    type VARCHAR(50),
    is_rotten BIGINT,
    FOREIGN KEY (owner_id) REFERENCES users(user_id),
    FOREIGN KEY (creator_id) REFERENCES users(user_id)
)""")

system.Database.execute_and_commit("""
CREATE TABLE IF NOT EXISTS egg_fights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    challenger_id VARCHAR(20),
    defender_id VARCHAR(20),
    chocolate_egg_bet INT,
    winner_id VARCHAR(20),
    FOREIGN KEY (challenger_id) REFERENCES users(user_id),
    FOREIGN KEY (defender_id) REFERENCES users(user_id),
    FOREIGN KEY (winner_id) REFERENCES users(user_id)
)""")

system.Database.execute_and_commit("""
CREATE TABLE IF NOT EXISTS group_fights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participants INT,
    chocolate_egg_bet INT,
    first_place_id VARCHAR(20),
    second_place_id VARCHAR(20),
    third_place_id VARCHAR(20),
    FOREIGN KEY (first_place_id) REFERENCES users(user_id),
    FOREIGN KEY (second_place_id) REFERENCES users(user_id),
    FOREIGN KEY (third_place_id) REFERENCES users(user_id)
)""")

system.Database.execute_and_commit("""
CREATE TABLE IF NOT EXISTS egg_throws (
    id INT AUTO_INCREMENT PRIMARY KEY,
    thrower_id VARCHAR(20),
    target_id VARCHAR(20),
    success BOOLEAN,
    FOREIGN KEY (thrower_id) REFERENCES users(user_id),
    FOREIGN KEY (target_id) REFERENCES users(user_id)
)""")

system.Database.execute_and_commit("""
CREATE TABLE IF NOT EXISTS cakes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)""")

system.Database.execute_and_commit("""
CREATE TABLE IF NOT EXISTS stats (
    stat VARCHAR(50) PRIMARY KEY,
    value INT DEFAULT 0
)""")

system.Database.execute_and_commit("""
Insert stats (stat, value) VALUES ('nests_found', 0), ('nests_searched', 0), ('deleted_cooked', 0), ('deleted_uncooked', 0), ('1', 0), ('2', 0), ('3', 0), ('4', 0), ('5', 0) ON DUPLICATE KEY UPDATE value = value
""")

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
    log(f"Token loaded: {bool(os.getenv('TOKEN'))}", "DEBUG")
    bot.run(os.getenv('TOKEN'))