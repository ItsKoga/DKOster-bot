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
                                      description="Sammle während des Events so viele Punkte wie möglich, suche <:Eier_Nest:1221556705490636880>, wirf andere mit :egg: ab, kämpfe gegen sie im Eierditschen und lasse :cake: von deiner Oma backen, um die Punkte zu sichern!", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="<:Schoko_Ei:1221556659030196284>", style=discord.ButtonStyle.gray)
            async def schoko(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title="<:Schoko_Ei:1221556659030196284> Schokoladenei", 
                                      description="<:Schoko_Ei:1221556659030196284> finden sich in <:Eier_Nest:1221556705490636880> und lassen sich zu :cake: verarbeiten, sodass diese nicht mehr gestohlen werden können. <:Schoko_Ei:1221556659030196284> ist 1 Punkt wert.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="🥚", style=discord.ButtonStyle.gray)
            async def osterei(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title=":egg: Rohes Ei", 
                                      description="Rohe Eier finden sich in <:Eier_Nest:1221556705490636880>, mit ihnen können andere Spieler abgeworfen werden, um <:Schoko_Ei:1221556659030196284> von diesen zu klauen. Außerdem werden sie benötigt, um einen :cake: zu backen. Es ist jedoch zu beachten, dass sie nach 3 Stunden verfaulen.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="<:osterei:962802014226640996>", style=discord.ButtonStyle.gray)
            async def gekocht(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title="<:osterei:962802014226640996> Gekochtes Ei", 
                                      description="Mit <:osterei:962802014226640996> lässt sich mit /fight Eierditschen spielen, sowie mit /groupfight ein Gruppenkampf starten. Gespielt wird um <:Schoko_Ei:1221556659030196284>, es kann eine beliebige Anzahl gesetzt werden. Bei einem normalen Eierditschen erhält der Gewinner alle <:Schoko_Ei:1221556659030196284>, bei einem Gruppenkampf der erste Platz 60% des Gesamteinsatzes, Platz 2 25% und Platz 3 15%. Wichtig zu beachten ist, dass die <:osterei:962802014226640996> nach einem Tag verfaulen.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="🍰", style=discord.ButtonStyle.gray)
            async def kuchen(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title=":cake: Kuchen", 
                                      description="Aus 10x <:Schoko_Ei:1221556659030196284> und 3x :egg: lässt sich von deiner Oma ein :cake: backen, welcher 10 Punkte wert ist. Deine Oma beschützt diesen Kuchen, sodass er nicht geklaut werden kann.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="⭐", style=discord.ButtonStyle.gray)
            async def special(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title=":star: Special Items", 
                                      description="- **Eiertalisman:** Dieser erhöht die Chance auf <:osterei:962802014226640996> oder :egg:, mit /talisman kann eingestellt werden welche Chance erhöht werden soll. Erhöht außerdem minimal die Anzahl der Eier pro Nest.\n\
- **Hasenpfote:** Eine Hasenpfote verdoppelt deine nächste Suche, du erhältst doppelt so viele Eier Hasenpfoten.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="🎫", style=discord.ButtonStyle.gray)
            async def tickets(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title=":ticket: Tickets", 
                                      description="Mit 🎫 nimmst du an einer Special Verlosung am Ende des Events teil, bei der du auch noch einmal Preise abstauben kannst. Ein 🎫 ist ein Eintrag in das Giveaway. 🎫 erhältst du durch /tickets.",
                                        color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                self.enable_all_items()
                button.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="Commands", style=discord.ButtonStyle.gray)
            async def commands(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Nutze doch /info um dir die Erklärung des Bots anzusehen!", ephemeral=True)
                embed = discord.Embed(title="Commands", 
                                      description="- **/collect:** Suche Ostereier im Garten\n\
- **/stats:** Zeigt die Stats eines Users an\n\
- **/leaderboard:** Zeigt die Top 10 der User an\n\
- **/fight:** Startet Eierditschen gegen einen User\n\
- **/groupfight:** Startet ein Gruppeneierditschen (Alle 5 Minuten möglich)\n\
- **/throw:** Wirf ein Ei ein :egg: auf einen anderen User, um diesem <:Schoko_Ei:1221556659030196284> zu klauen\n\
- **/bake:** Lässt deine Oma einen :cake: backen\n\
- **/talisman:** Wähle aus ob du mehr <:osterei:962802014226640996> oder :egg: finden möchtest\n\
- **/notify:** Ändert die Benachrichtigungseinstellungen\n\
- **/tickets:** Tausche <:osterei:962802014226640996> für :ticket:", color=0xec6726)  
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
        
        await ctx.response.send_message(embed=embed, view=view, ephemeral=True)
        log("/info : Nachricht gesendet")

            


def setup(bot):
    bot.add_cog(Info(bot))