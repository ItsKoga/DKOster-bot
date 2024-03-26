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

        @tasks.loop(seconds=5)
        async def update_lb():
            system.Update.leaderboard(25)
        
        update_lb.start()


    @slash_command(name="stats", description="Zeigt die Stats eines Users an")
    async def stats(self, ctx, user: discord.User = None):
        user = user if user else ctx.author
        log(f"{ctx.author.name} hat die Stats von {user.name} angefordert!", "USER_ACTION")

        profile = system.Get.user(user.id)
        chocolate_eggs = system.Get.type_eggs(user.id, "Schokoei")
        cakes = len(system.Get.cakes(user.id))
        cooked = len([egg for egg in system.Get.type_eggs(user.id, "gekochtes Hühnerei") if egg.is_rotten == False])
        uncooked = len([egg for egg in system.Get.type_eggs(user.id, "ungekochtes Hühnerei") if egg.is_rotten == False])
        hits = system.Get.hits(user.id)
        throws = system.Get.own_throws(user.id)
        throws = throws if throws else []
        own_hits = [throw for throw in throws if throw.success == True] if throws else []
        points = system.Get.points(user.id)

        last_hit = f"<t:{profile.last_hit}:R>" if profile.last_hit != 0 else "Nie"

        embed = discord.Embed(title=f"Stats von {user.display_name}", 
                              description= f"Punkte : {points}\n\
<:Schoko_Ei:1221556659030196284> : {chocolate_eggs}\n\
:cake: : {cakes}\n\
:egg: : {uncooked}\n\
<:osterei:962802014226640996> : {cooked}\n\
Zuletzt getroffen : {last_hit}\n\
Würfe : {len(throws)}/{len(own_hits)} `{round(100/len(throws)*len(own_hits) if throws else 0,1)}%`\n\
Abgeworfen : {hits[0]}/{hits[1]} `{round(100/hits[0]*hits[1]if hits[0] else 0,1)}%`", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")

        await ctx.response.send_message(embed=embed)




    @slash_command(name="leaderboard", description="Zeigt die Top 10 der User an")
    async def leaderboard(self, ctx):
        log(f"{ctx.author.name} hat die Leaderboard angefordert!", "USER_ACTION")

        embed = discord.Embed(title="Leaderboard", description=system.Translate.leaderboard(10) + f"\n\n{system.Get.top_position(ctx.author.id)}. Du - {system.Get.points(ctx.author.id)}", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")

        await ctx.response.send_message(embed=embed)




def setup(bot):
    bot.add_cog(Stats(bot))