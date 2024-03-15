import discord
from discord.ext import commands, tasks
from discord.commands import slash_command, Option

import time as tm
import asyncio

import os

import log_helper
import system

log = log_helper.create("Stats")


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = tm.time()


    @slash_command(name="stats", description="Zeigt die Stats eines Users an")
    async def stats(self, ctx, user: discord.Member = None):
        user = user if user else ctx.author

        profile = system.Get.user(user.id)
        hits = system.Get.hits(user.id)
        throws = system.Get.own_throws(user.id)
        own_hits = [throw for throw in throws if throw.success == True]
        points = system.Get.points(user.id)

        embed = discord.Embed(title="Stats", color=discord.Color.blurple())
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(name=f"Stats von {user.name}", value=f"Punkte : {points}\n\
Zuletzt getroffen : <t:{profile.last_hit}:R>\n\
Würfe : {len(throws)}/{len(own_hits)} `{round(len(throws)/len(own_hits),1)}%`\n\
Abgeworfen : {hits[0]}/{hits[1]} `{round(hits[0]/hits[1],1)}%`", inline=True)
        embed.set_footer(text=f"Made by ItsKoga ❤")





def setup(bot):
    bot.add_cog(Stats(bot))