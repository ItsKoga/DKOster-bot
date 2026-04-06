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
            await system.Update.leaderboard(25)
        
        update_lb.start()


    @slash_command(name="stats", description="Zeigt die Stats eines Users an", guild_only=True)
    async def stats(self, ctx, user: discord.User = None):
        user = user if user else ctx.author
        log(f"{ctx.author.name} hat die Stats von {user.name} angefordert!", "USER_ACTION")

        profile = await system.Get.user(user.id)
        chocolate_eggs = profile.chocolate_eggs
        cakes = profile.cakes
        cooked = len([egg for egg in await system.Get.type_eggs(user.id, "gekochtes Hühnerei") if egg.is_rotten == False])
        uncooked = len([egg for egg in await system.Get.type_eggs(user.id, "ungekochtes Hühnerei") if egg.is_rotten == False])
        hits = profile.eggs_hit
        throws = profile.eggs_throwen
        own_throws = profile.eggs_throwen_at
        own_hits = profile.eggs_hit_at
        times_collected = await system.Get.user_collect_amount(user.id)
        nests_found = await system.Get.user_found_nests(user.id)
        points = system.format_number(await system.Get.points(user.id))
        rabbit_foot_amount = await system.Get.rabbit_foot_amount(user.id)
        used_rabbit_foot_amount = await system.Get.used_rabbit_foot_amount(user.id)
        tickets = await system.Get.tickets(user.id)

        last_hit = f"<t:{profile.last_hit}:R>" if profile.last_hit != 0 else "Nie"

        embed = discord.Embed(title=f"Statistiken von {user.display_name}", color=0xec6726)
        embed.add_field(name="Punkte", value=f"{points} (#{await system.Get.top_position(user.id)})", inline=False)
        embed.add_field(name="Eier", value=f"<:Schoko_Ei:1221556659030196284>: {chocolate_eggs}\n"
                           f":egg:: {uncooked}\n"
                           f"<:osterei:962802014226640996>: {cooked}", inline=True)
        embed.add_field(name="Kuchen", value=f":cake: {cakes}", inline=True)
        embed.add_field(name="Hasenpfoten", value=f":ticket: : {tickets}\n"
                              f"Hasenpfoten: {rabbit_foot_amount}\n"
                              f"Benutzte Hasenpfoten: {used_rabbit_foot_amount}\n", inline=True)
        embed.add_field(name="Aktionen", value=f"Zuletzt getroffen: {last_hit}\n"
                               f"Abgeworfen: {own_throws}\n"
                               f"Getroffen: {own_hits}\n"
                               f"Jemanden abgeworfen: {throws}\n"
                               f"Jemanden getroffen: {hits}", inline=False)
        embed.add_field(name="Sammlung", value=f"/collect ausgeführt: {times_collected}\n"
                               f"Nester gefunden: {nests_found}", inline=False)
        embed.set_footer(text="Made by ItsKoga ❤")

        await ctx.response.send_message(embed=embed, ephemeral=True)




    @slash_command(name="leaderboard", description="Zeigt die Top 10 der User an", guild_only=True)
    async def leaderboard(self, ctx):
        log(f"{ctx.author.name} hat die Leaderboard angefordert!", "USER_ACTION")

        points = system.format_number(await system.Get.points(ctx.author.id))

        leaderboard_data = await system.Translate.leaderboard(10)
        user_position = await system.Get.top_position(ctx.author.id)
        embed = discord.Embed(title="🏆 Leaderboard", color=0xec6726)
        embed.add_field(name="Top 10 Spieler", value=leaderboard_data, inline=False)
        embed.add_field(name="Deine Position", value=f"{user_position}. Du - {points}", inline=False)
        embed.set_footer(text="Made by ItsKoga ❤")

        await ctx.response.send_message(embed=embed, ephemeral=True)



def setup(bot):
    bot.add_cog(Stats(bot))