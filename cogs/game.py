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
        log(f"{ctx.author.name} hat nach Eiern gesucht!", "USER_ACTION")
        embed = discord.Embed(title="Eiersuche", description="Wo willst du suchen", color=0xec6726)
        embed.set_image(url="https://i.imgur.com/AsSh0xY.png")
        embed.set_footer(text=f"Made by ItsKoga ❤")
    
        locations = {}
        for location in ("1", "2", "3", "4", "5"):
            locations[location] = system.Gen.nest(location, ctx)
                        
        view = discord.ui.View()

        for location in locations:
            button = discord.ui.Button(label=location, style=discord.ButtonStyle.primary, custom_id=location)
            async def callback(interaction: discord.Interaction, location=locations[location]):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("Du kannst nicht für andere Leute sammeln!", ephemeral=True)
                await interaction.message.edit(view=None)
                embed = discord.Embed(title="Eiersuche", description=f"**<:Eier_Nest:1221556705490636880> {location.location}** (Deine Suche):\n{system.Translate.nest(location)}",color=0xec6726)
                for location_ in locations:
                    if location_ != location.location:
                        embed.add_field(name="<:Eier_Nest:1221556705490636880> "+location_ + (f" ({locations[location_].type})" if locations[location_].type != 'empty' else ' (leer)'), value=system.Translate.nest(locations[location_]), inline=True)
                    else:
                        rewards = locations[location_]

                embed.set_footer(text=f"Made by ItsKoga ❤")

                await interaction.response.send_message(interaction.user.mention,embed=embed)

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

                if system.Get.rabbit_foot_check(ctx.author.id):
                    system.Update.user_remove_one_rabbit_foot_count(ctx.author.id)
                
                log(f"{ctx.author.name} wurden die Belohnungen hinzugefügt!", "SUCCESS")
                system.Get.points(ctx.author.id)

                await asyncio.sleep(120)
                embed = discord.Embed(title="Du kannst wieder /collect ausführen!", description="Es ist fünf Minuten her, seitdem du Pukte für das Oster-Event gesammelt hast.\n\
Führe jetzt wieder /collect im Channel <#platzhalter> aus!\n\n\
Du möchtest keine Benachrichtigungen mehr erhalten? Dann deaktiviere den Ping einfach mit dem /nofify Befehl.", color=discord.Color.random())
                embed.set_footer(text=f"Made by ItsKoga ❤")
                if system.Get.notifications(ctx.author.id):
                    await interaction.user.send(embed=embed)

                

            button.callback = callback
            view.add_item(button)

        await ctx.response.send_message(embed=embed, view=view)


        

    @slash_command(name="throw", description="Wirf ein Ei auf jemanden")
    async def throw(self, ctx, user: discord.User):
        if ctx.author.id == user.id:
            return await ctx.response.send_message("Du kannst nicht auf dich selbst werfen!", ephemeral=True)
        if user.bot:
            return await ctx.response.send_message("Du kannst nicht auf Bots werfen!", ephemeral=True)
        check = system.Get.egg_check(ctx.author.id, "ungekochtes Hühnerei")
        if check == False:
            return await ctx.response.send_message("Du hast keine ungekochten Hühnereier!", ephemeral=True)
        if system.Get.user(user.id).last_hit > tm.time()-300:
            return await ctx.response.send_message("Dieser User wurde in den letzen 5 Minuten bereits abgeworfen!", ephemeral=True)
        log(f"{ctx.author.name} hat ein Ei auf {user.name} geworfen!", "USER_ACTION")
        
        success = random.choice([0, 1])
        system.Add.throw(ctx.author.id, user.id, success)
        if success == 0:
            embed = discord.Embed(title="Eierwurf", description=f"Du hast ein Ei auf {user.name} geworfen, aber es ist daneben gegangen!", color=discord.Color.red())

        else:
            points = system.Get.points(user.id)
            percent = random.choices([1, 2, 3, 4, 5], weights=[0.5, 0.4, 0.3, 0.2, 0.1])[0]
            reward = int(points/100*percent)

            eggs = system.Get.type_eggs(ctx.user.id, "Schokoei")
            for i in range(reward):
                if eggs[i]:
                    system.Update.egg_owner(eggs[i].id, user.id)
                else:
                    reward = i 
                    embed = discord.Embed(title="Eierwurf", description=f"Du hast ein Ei auf {user.name} geworfen und getroffen! Du hast {reward}`{percent}%` Schokoeier erhalten! Der rest war bei der Oma.", color=discord.Color.green())
            
            system.Update.user_last_hit(user.id)
            system.Delete.egg(check.id)

            if not embed:
                embed = discord.Embed(title="Eierwurf", description=f"Du hast ein Ei auf {user.name} geworfen und getroffen! Du hast {reward}`{percent}%` Schokoeier erhalten!", color=discord.Color.green())
                
        embed.set_footer(text=f"Made by ItsKoga ❤")
        await ctx.response.send_message(user.mention,embed=embed)
        system.Get.points(ctx.author.id)
        

    @slash_command(name="fight", description="Fordere jemanden zum Kampf heraus")
    async def fight(self, ctx, user: discord.User, bet: int):
        if ctx.author.id == user.id:
            return await ctx.response.send_message("Du kannst nicht gegen dich selbst kämpfen!", ephemeral=True)
        if user.bot:
            return await ctx.response.send_message("Du kannst nicht gegen Bots kämpfen!", ephemeral=True)
        if bet < 1:
            return await ctx.response.send_message("Du musst mindestens 1 <:Schoko_Ei:1221556659030196284> setzen!", ephemeral=True)
        if len(system.Get.type_eggs(ctx.author.id, "Schokoei")) < bet:
            return await ctx.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if len(system.Get.type_eggs(user.id, "Schokoei")) < bet:
            return await ctx.response.send_message("Dein Gegner hat nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if system.Get.egg_check(ctx.author.id, "gekochtes Hühnerei") == False:
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        if system.Get.egg_check(user.id, "gekochtes Hühnerei") == False:
            return await ctx.response.send_message("Dein Gegner hat kein <:osterei:962802014226640996>!", ephemeral=True)
        log(f"{ctx.author.name} hat {user.name} zum Kampf herausgefordert!", "USER_ACTION")

        embed = discord.Embed(title="Kampf Anfrage", description=f"{ctx.author.mention} hat dich zu einem Kampf herausgefordert! Möchtest du annehmen?", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = None

            @discord.ui.button(label="Annehmen", style=discord.ButtonStyle.success)
            async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = True
                self.disable_all_items()
                await interaction.message.edit(view=self)

                winner = random.choice([ctx.author.id, user.id])
                looser = ctx.author.id if winner == user.id else user.id
                embed = discord.Embed(title="Kampf", description=f"{ctx.author.mention} und {user.mention} kämpfen!", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await interaction.response.send_message(embed=embed)

                system.Add.solo_fight(ctx.author.id, user.id, bet, winner)
                eggs = system.Get.type_eggs(ctx.author.id, "Schokoei")

                if len(eggs) < bet:
                    embed = discord.Embed(title="Error", description=f"{ctx.author.mention} hat nicht mehr genug <:Schoko_Ei:1221556659030196284>!", color=discord.Color.red())
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    return await interaction.original_response.edit_message(embed=embed)
                
                for i in range(bet):
                    system.Update.egg_owner(eggs[i].id, winner)
                system.Delete.egg(system.Get.egg_check(looser, "gekochtes Hühnerei").id)
                        
                await asyncio.sleep(5)
                embed = discord.Embed(title="Kampf", description=f"<@{winner}> hat den Kampf gewonnen!\n\
Er erhält {bet}x <:osterei:962802014226640996> von <@{looser}>.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await interaction.edit_original_response(embed=embed)
            
            
            @discord.ui.button(label="Ablehnen", style=discord.ButtonStyle.danger)
            async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = False
                self.disable_all_items()
                await interaction.message.edit(view=self)
                await interaction.response.send_message("Kampf Anfrage wurde abgelehnt!",)

        view = View()
        await ctx.response.send_message(user.mention, embed=embed, view=view)
        system.Get.points(ctx.author.id)
        system.Get.points(user.id)

        

    #Need to add the group_fight command here
    @slash_command(name="group_fight", description="Starte einen Gruppenkampf")
    async def group_fight(self, ctx, bet: int):
        if bet < 1:
            return await ctx.response.send_message("Du musst mindestens 1 <:Schoko_Ei:1221556659030196284> setzen!", ephemeral=True)
        if len(system.Get.type_eggs(ctx.author.id, "Schokoei")) < bet:
            return await ctx.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if system.Get.egg_check(ctx.author.id, "gekochtes Hühnerei") == False:
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        log(f"{ctx.author.name} hat einen Gruppenkampf gestartet!", "USER_ACTION")

        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = []
                self.timeout = 60

            async def on_timeout(self):
                await self.edit_original_response(view=None)
                if len(self.value) < 4:
                    return await ctx.response.send_message("Nicht genug Spieler für den Gruppenkampf!", ephemeral=True)
                
                embed = discord.Embed(title="Gruppenkampf", description=f"Der Gruppenkampf beginnt!", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await ctx.response.send_message(embed=embed)
                rewards = [int(bet*0.6), int(bet*0.25), int(bet*0.15)]
                if sum(rewards) < bet*len(self.value):
                    rewards[0] += sum(rewards) - bet*len(self.value)
                if sum(rewards) > bet*len(self.value):
                    rewards[0] += sum(rewards) - bet*len(self.value)
                top = []
                while len(self.value) > 1:
                    player1 = random.choice(self.value)
                    player2 = random.choice([player for player in self.value if player != player1])
                    winner = random.choice([player1, player2])
                    looser = player1 if winner == player2 else player2
                    top.append(looser)
                    self.value.remove(looser)
                    system.Delete.egg(system.Get.egg_check(looser, "gekochtes Hühnerei").id)
                    embed = discord.Embed(title="Gruppenkampf", description=f"<@{player1}> und <@{player2}> kämpfen!", color=0xec6726)
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    if not msg:
                        msg = await self.original_response.respond(embed=embed)
                    else:
                        await msg.edit(embed=embed)
                    await asyncio.sleep(3)

                    embed = discord.Embed(title="Gruppenkampf", description=f"<@{winner}> hat den Kampf gewonnen!\n\
<@{looser}> ist auf Platz {len(self.value)+1} ausgeschieden!", color=0xec6726)

                    await msg.edit(embed=embed)
                    self.value.remove(looser)
                    await asyncio.sleep(3)

                embed = discord.Embed(title="Gruppenkampf", description=f"<@{self.value[0]}> hat den Gruppenkampf gewonnen!\n\
Er erhält {rewards[0]}x <:Schoko_Ei:1221556659030196284>!", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await msg.edit(embed=embed)

                participants = [self.value[0]] + top
                eggs = []
                for i in range(len(participants)):
                    for j in range(rewards[i]):
                        eggs.append(participants[i])

                for i in range(3):
                    for j in range(rewards[i]):
                        system.Update.egg_owner(eggs[0].id, participants[i])
                        eggs.remove(eggs[0])
                    system.Get.points(participants[i])

                embed = discord.Embed(title="Gruppenkampf", description=f"<@{self.value[0]}> hat den Gruppenkampf gewonnen!\n\
Er erhält {rewards[0]}x <:Schoko_Ei:1221556659030196284>!\n\
<@{top[0]}> erhält {rewards[1]}x <:Schoko_Ei:1221556659030196284>!\n\
<@{top[1]}> erhält {rewards[2]}x <:Schoko_Ei:1221556659030196284>!", color=discord.Color.green())
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await ctx.response.send_message(embed=embed)

    #Notiz an mich: Beim debuggen darauf achten nicht springen zu gehen
                



            @discord.ui.button(label="Beitreten", style=discord.ButtonStyle.primary)
            async def join(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id in self.value:
                    return await interaction.response.send_message("Du bist bereits beigetreten!", ephemeral=True)
                if not system.Get.group_fight_check(interaction.user.id):
                    return await interaction.response.send_message("Du hast in den letzten 5 Minuten bereits an einem Gruppenkampf teilgenommen!", ephemeral=True)
                if len(system.Get.type_eggs(interaction.user.id, "Schokoei")) < bet:
                    return await interaction.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
                if system.Get.egg_check(interaction.user.id, "gekochtes Hühnerei") == False:
                    return await interaction.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
                self.value.append(interaction.user.id)
                await interaction.response.send_message("Du bist dem Gruppenkampf beigetreten!", ephemeral=True)
                system.Update.last_fight(interaction.user.id)

        embed = discord.Embed(title="Gruppenkampf", description=f"{ctx.author.mention} hat einen Gruppenkampf gestartet! Möchtest du beitreten?", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        view = View()
        await ctx.response.send_message(embed=embed, view=view)



    @slash_command(name="bake", description="Backe ein gekochtes Hühnerei")
    async def bake(self, ctx):
        check = system.Get.bake_check(ctx.author.id)
        if check == False:
            embed = discord.Embed(title="Kuchen backen", description="Du hast nicht alle Zutaten, daher kann dir deine Oma nicht helfen!", color=discord.Color.red())
            embed.add_field(name="Zutaten", value="3x Ungekochtes Hühnerei\n10x Schokoei")
            embed.set_footer(text=f"Made by ItsKoga ❤")
            return await ctx.response.send_message(embed=embed)
        log(f"{ctx.author.name} hat ein kuchen gebacken!", "USER_ACTION")
        system.Update.bake(ctx.author.id)
        embed = discord.Embed(title="Kuchen backen", description="Deine Oma hat dir geholfen einen Kuchen zu backen! Da niemand von einer Oma klaut sind deine Punkte sicher!", color=discord.Color.green())
        await ctx.response.send_message(embed=embed)
        system.Get.points(ctx.author.id)
        

    @slash_command(name="talisman", description="Zeigt dir deinen Eier Talisman")
    async def talisman(self, ctx, richtung: Option(str, "Wähle welche Chance dein Talisman erhöhen soll", choices=["gekochtes Hühnerei", "ungekochtes Hühnerei"])):
        profile = system.Get.user(ctx.author.id)
        if profile.egg_talisman == 0:
            return await ctx.response.send_message("Du hast noch keinen Eier Talisman!", ephemeral=True)
        if richtung == "gekochtes Hühnerei":
            system.Update.user_egg_talisman(ctx.author.id, 2)
            await ctx.response.send_message("Dein Eier Talisman erhöht jetzt die Chance auf gekochte Hühnereier!", ephemeral=True)
        else:
            system.Update.user_egg_talisman(ctx.author.id, 1)
            await ctx.response.send_message("Dein Eier Talisman erhöht jetzt die Chance auf ungekochte Hühnereier!", ephemeral=True)
        log(f"{ctx.author.name} hat seinen Talisman geändert!", "USER_ACTION")
            

        
def setup(bot):
    bot.add_cog(Game(bot))
