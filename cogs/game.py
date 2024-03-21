import discord
from discord.ext import commands, tasks
from discord.commands import slash_command, Option

import os

import log_helper
import system
import random

import time as tm

log = log_helper.create("Game")


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
        
            if 0 <= tm.localtime().tm_hour < 6 and ctx.command.name != "leaderboard":
                await ctx.response.send_message("Momentan versteckt der Osterhase neue Eier! Du kannst dich also bis 6:00 Uhr schlafen legen.", ephemeral=True)

            if ctx.command.name == "collect":
                await ctx.response.send_message(f"Du kannst erst <t:{int(tm.time()+error.retry_after)}:R> wieder nach Eiern suchen!", ephemeral=True)

            else:
                await ctx.response.send_message(f"So ein Pech! Du kannst erst <t:{int(tm.time()+error.retry_after)}:R> wieder `/{ctx.command.name}` nutzen!", ephemeral=True)

    @slash_command(name="collect", description="Geh auf Eiersuche")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def collect(self, ctx):
        embed = discord.Embed(title="Eiersuche", description="Wo willst du suchen", color=discord.Color.blurple())
        embed.set_image(url="https://i.imgur.com/maC8seb.png")
        embed.set_footer(text=f"Made by ItsKoga ❤")
    
        locations = {}
        for location in ("Wald", "Wiese", "Höhle", "Hügel", "Teich"):
            type = random.choices(["empty", "normal", "special"], weights=[0.5, 0.4, 0.1])[0]
            if type == "empty":
                locations[location] = system.Gen.nest(location=location, type="empty")
            elif type == "normal":
                locations[location] = system.Gen.nest(location=location, type="normal",
                                                           schokoei=random.randint(1, 10),
                                                           gekochtesEi=0 if random.random() < 0.9 else random.randint(1, 2),
                                                           ungekochtesEi=0 if random.random() < 0.1 else random.randint(1, 2))
            elif type == "special":
                locations[location] = system.Gen.nest(location=location, type="special",
                                                           schokoei=random.randint(1, 10),
                                                           gekochtesEi=random.randint(1, 2) if random.random() <= 0.9 else 0,
                                                           ungekochtesEi=random.randint(1, 2) if random.random() <= 0.1 else 0,
                                                           egg_talisman=1 if system.Get.user(ctx.author.id).egg_talisman or random.random() <= 0.1 else 0,
                                                           rabbit_foot_count=1 if random.random() <= 0.25 else 0)
                        
        view = discord.ui.View()

        for location in locations:
            button = discord.ui.Button(label=location, style=discord.ButtonStyle.primary, custom_id=location)
            async def callback(interaction: discord.Interaction, location=locations[location]):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("Du kannst nicht für andere Leute sammeln!", ephemeral=True)
                await interaction.message.edit(view=None)
                embed = discord.Embed(title="Eiersuche", description=f"**{location.location}** (Deine Suche):\n{system.Translate.nest(location)}",color=discord.Color.blurple())
                for location_ in locations:
                    if location_ != location.location:
                        embed.add_field(name=location_ + (f" ({locations[location_].type})" if locations[location_].type != 'empty' else ' (leer)'), value=system.Translate.nest(locations[location_]), inline=True)
                    else:
                        rewards = locations[location_]

                embed.set_footer(text=f"Made by ItsKoga ❤")

                await interaction.response.send_message(embed=embed)

                log(f"{ctx.author.name} hat {rewards.schokoei} Schokoeier, {rewards.gekochtesEi} gekochte Hühnereier, {rewards.ungekochtesEi} ungekochte Hühnereier, {rewards.egg_talisman} Eier Talisman und {rewards.rabbit_foot_count} Hasenpfoten gefunden!")        
               
                for i in range(rewards.schokoei):
                    system.Add.egg(ctx.author.id, "Schokoei")
                for i in range(rewards.gekochtesEi):
                    system.Add.egg(ctx.author.id, "gekochtes Hühnerei")
                for i in range(rewards.ungekochtesEi):
                    system.Add.egg(ctx.author.id, "ungekochtes Hühnerei")
                if rewards.egg_talisman:
                    system.Update.user_egg_talisman(ctx.author.id, 1)
                if rewards.rabbit_foot_count:
                    system.Update.user_add_one_rabbit_foot_count(ctx.author.id)
                
                log(f"{ctx.author.name} wurden die Belohnungen hinzugefügt!", "SUCCESS")

                

            button.callback = callback
            view.add_item(button)

        await ctx.response.send_message(embed=embed, view=view)




        

    #Need to add the throw command here
        

    #Need to add the fight command here
        

    #Need to add the group_fight command here
        

    #Need to add the bake command here
        

    #Need to add the talisman command here
        

    
def setup(bot):
    bot.add_cog(Game(bot))