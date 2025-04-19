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


    @slash_command(name="stats", description="Zeigt die Stats eines Users an", guild_only=True)
    async def stats(self, ctx, user: discord.User = None):
        user = user if user else ctx.author
        log(f"{ctx.author.name} hat die Stats von {user.name} angefordert!", "USER_ACTION")

        profile = system.Get.user(user.id)
        chocolate_eggs = system.format_number(len(system.Get.type_eggs(user.id, "Schokoei")))
        cakes = len(system.Get.cakes(user.id))
        cooked = len([egg for egg in system.Get.type_eggs(user.id, "gekochtes Hühnerei") if egg.is_rotten == False])
        uncooked = len([egg for egg in system.Get.type_eggs(user.id, "ungekochtes Hühnerei") if egg.is_rotten == False])
        hits = system.Get.hits(user.id)
        throws = system.Get.own_throws(user.id)
        own_hits = [throw for throw in throws if throw.success == True] if throws else []
        times_collected = system.Get. user_collect_amount(user.id)
        nests_found = system.Get.user_found_nests(user.id)
        points = system.format_number(system.Get.points(user.id))
        rabbit_foot_amount = system.Get.rabbit_foot_amount(user.id)
        used_rabbit_foot_amount = system.Get.used_rabbit_foot_amount(user.id)
        tickets = system.Get.tickets(user.id)

        last_hit = f"<t:{profile.last_hit}:R>" if profile.last_hit != 0 else "Nie"

        embed = discord.Embed(title=f"Statistiken von {user.display_name}", color=0xec6726)
        embed.add_field(name="Punkte", value=f"{points} (#{system.Get.top_position(user.id)})", inline=False)
        embed.add_field(name="Eier", value=f"<:Schoko_Ei:1221556659030196284>: {chocolate_eggs}\n"
                           f":egg:: {uncooked}\n"
                           f"<:osterei:962802014226640996>: {cooked}", inline=True)
        embed.add_field(name="Kuchen", value=f":cake: {cakes}", inline=True)
        embed.add_field(name="Hasenpfoten", value=f":ticket: : {tickets}\n"
                              f"Hasenpfoten: {rabbit_foot_amount}\n"
                              f"Benutzte Hasenpfoten: {used_rabbit_foot_amount}\n", inline=True)
        embed.add_field(name="Aktionen", value=f"Zuletzt getroffen: {last_hit}\n"
                               f"Abgeworfen worden: {hits[0]}\n"
                               f"Getroffen worden: {hits[1]}\n"
                               f"Jemanden abgeworfen: {len(throws)}\n"
                               f"Jemanden getroffen: {len(own_hits)}", inline=False)
        embed.add_field(name="Sammlung", value=f"/collect ausgeführt: {times_collected}\n"
                               f"Nester gefunden: {nests_found}", inline=False)
        embed.set_footer(text="Made by ItsKoga ❤")

        await ctx.response.send_message(embed=embed, ephemeral=True)




    @slash_command(name="leaderboard", description="Zeigt die Top 10 der User an", guild_only=True)
    async def leaderboard(self, ctx):
        log(f"{ctx.author.name} hat die Leaderboard angefordert!", "USER_ACTION")

        points = system.format_number(system.Get.points(ctx.author.id))

        leaderboard_data = system.Translate.leaderboard(10)
        user_position = system.Get.top_position(ctx.author.id)
        embed = discord.Embed(title="🏆 Leaderboard", color=0xec6726)
        embed.add_field(name="Top 10 Spieler", value=leaderboard_data, inline=False)
        embed.add_field(name="Deine Position", value=f"{user_position}. Du - {points}", inline=False)
        embed.set_footer(text="Made by ItsKoga ❤")

        await ctx.response.send_message(embed=embed, ephemeral=True)



def setup(bot):
    bot.add_cog(Stats(bot))