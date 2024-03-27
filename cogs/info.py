import discord
from discord.ext import commands, tasks
from discord.commands import slash_command, Option

import time as tm
import asyncio

import os

import log_helper
import system

log = log_helper.create("Info")


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="info", description="Zeigt die Erklärung des Bots an", guild_only=True)
    async def info(self, ctx):
        log(f"{ctx.author.name} hat /info ausgeführt!", "USER_ACTION")
        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = ctx.author.id
                self.timeout = 60

            @discord.ui.button(emoji="<:info:1032012910702104687>", style=discord.ButtonStyle.gray)
            async def info(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title="<:info:1032012910702104687> Osterevent", 
                                      description="Sammle während des Events so viele Punkte wie möglich, suche Osternester, wirf andere mit Eiern ab, kämpfe gegen sie im Eierditschen und lasse Kuchen von deiner Oma backen, um die Punkte zu sichern!", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji=":Schoko_Ei:1221556659030196284>", style=discord.ButtonStyle.gray)
            async def schoko(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title="<:Schoko_Ei:1221556659030196284> Schokoladenei", 
                                      description="Schokoladeneier finden sich in Osternestern und lassen sich zu Kuchen verarbeiten, sodass diese nicht mehr gestohlen werden können. Ein Schokoladenei ist 1 Punkt wert.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="🥚", style=discord.ButtonStyle.gray)
            async def osterei(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title=":egg: Rohes Ei", 
                                      description="Rohe Eier finden sich in Osternestern, mit ihnen können andere Spieler abgeworfen werden um Schokoeier von diesen zu klauen. Außerdem werden sie benötigt um einen Kuchen zu backen.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="<:osterei:962802014226640996>", style=discord.ButtonStyle.gray)
            async def gekocht(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title="<:osterei:962802014226640996> Gekochtes Ei", 
                                      description="Mit diesen Eiern lässt sich mit /fight Eierditschen spielen, sowieo mit /groupfight ein Gruppenkampf starten. Gespielt wird um Schokoeier, es kann eine beliebige Anzahl gesetzt werden. Bei einem normalen Eierditschen erhält der Gewinner alle Schokoeier, bei einem Gruppenkampf der erste Platz 60% des Gesamteinsatzes, Platz 2 25% und Platz 3 15%", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="🍰", style=discord.ButtonStyle.gray)
            async def kuchen(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title=":cake: Kuchen", 
                                      description="Aus 10 Schokoladeneiern und 3 Rohen Eiern lässt sich von deiner Oma ein Kuchen backen, welcher 10 Punkte wert ist. Deine Oma beschützt diesen Kuchen, sodass er nicht geklaut werden kann.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="⭐", style=discord.ButtonStyle.gray)
            async def special(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title=":star: Special Items", 
                                      description="- **Eiertalisman:** Dieser erhöht die Chance auf gekochte oder ungekochte Eier, mit /talisman kann eingestellt werden welche Chance erhöht werden soll. Erhöht außerdem minimal die Anzahl der Eier pro Nest.\n\
- **Hasenpfote:** Mit /hasenpfote kann diese eingesetzt werden und verdoppelt die Eier bei der nächsten Suche.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            async def on_timeout(self):
                self.disable_all_items()
                await self.message.edit(view=self)

        view = View()
        log("/info : View erstellt")
        view.children[0].disabled = True

        embed = discord.Embed(title="<:info:1032012910702104687> Osterevent", 
                              description="Sammle während des Events so viele Punkte wie möglich, suche Osternester, wirf andere mit Eiern ab, kämpfe gegen sie im Eierditschen und lasse Kuchen von deiner Oma backen, um die Punkte zu sichern!", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        log("/info : Embed erstellt")
        
        await ctx.response.send_message(embed=embed, view=view)
        log("/info : Nachricht gesendet")

            


def setup(bot):
    bot.add_cog(Info(bot))