import discord
from discord.ext import commands, tasks
from discord.commands import slash_command, Option

import os
import math
import asyncio

import log_helper
import system
import random

import time as tm
import discord

log = log_helper.create("Settings")


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="notify", description="Schaltet die Benachrichtigungen an oder aus")
    async def notify(self, ctx):
        log(f"{ctx.author.name} hat die Benachrichtigungen umgestellt!", "USER_ACTION")

        await ctx.response.send_message(f"Benachrichtigungen wurden {'aktiviert' if not system.Get.notifications(ctx.author.id) else 'deaktiviert'}!", ephemeral=True)
        system.Update.user_notifications(ctx.author.id, not system.Get.notifications(ctx.author.id))


        
def setup(bot):
    bot.add_cog(Settings(bot))
