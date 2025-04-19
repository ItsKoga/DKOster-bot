import discord
from discord.ext import commands, tasks
from discord.commands import slash_command, Option

import os
import math
import asyncio

import log_helper
import system

import random
import requests

import time as tm
import discord

log = log_helper.create("Game")
group_fight_running = False



def is_verified():
    def verified(ctx):
        url = f"https://combi.dev/API/CheckVerification?ID={ctx.author.id}&key={os.getenv('COMBI_API_KEY')}"
        response = requests.get(url).json()
        log(f"Verifizierung Anfrage: {response}", "SYSTEM")
        if response["success"] == False:
            log(f"Bei der Verifizierung Anfrage ist ein Fehler aufgetreten! {response}", "CRITICAL")
            return True
        if response["verified"]:
            log(f"{ctx.author.name} ist verifiziert!", "USER_ACTION")
            return True
        log(f"{ctx.author.name} ist nicht verifiziert!", "ERROR")
        return False
    return commands.check(verified)


# Normal (22:00 Uhr)
def is_day():
    def day(ctx):
        time = tm.localtime()
        if time.tm_hour < 6 or time.tm_hour > 23:
            return False
        return True
    return commands.check(day)

# Ende (20:00 Uhr)
#def is_day():
#    def day(ctx):
#        time = tm.localtime()
#        if time.tm_hour < 6 or time.tm_hour > 21:
#            return False
#        return True
#    return commands.check(day)

# Start 6:00 Uhr Aktuell nach 15 Uhr
#def is_day():
#    def day(ctx):
#        time = tm.localtime()
#        print(time.tm_hour)
#        if time.tm_hour < 6 or time.tm_hour > 15:
#            return False
#        return True
#    return commands.check(day)



class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        log(f"Fehler bei {ctx.command.name}: {error}", "ERROR")
        if isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name == "collect":
                embed = discord.Embed(title="Eiersuche", description=f"Du kannst erst <t:{int(tm.time()+error.retry_after)}:R> wieder nach Eiern suchen!", color=discord.Color.red())
                embed.set_footer(text=f"Made by ItsKoga ❤")
                return await ctx.response.send_message(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(title="Fehler", description=f"Du kannst erst <t:{int(tm.time()+error.retry_after)}:R> wieder `/{ctx.command.name}` nutzen!", color=discord.Color.red())
                embed.set_footer(text=f"Made by ItsKoga ❤")
                return await ctx.response.send_message(embed=embed, ephemeral=True)

        time = tm.localtime()
# Normal (22:00 Uhr)
        if time.tm_hour < 6 or time.tm_hour > 23:
            embed = discord.Embed(title="Fehler", description="Der Osterhase versteckt zwischen 0:00 und 6:00 Uhr neue Eier, aus diesem Grund hat deine Oma dich ins Bett geschickt!", color=discord.Color.red())
            embed.set_footer(text=f"Made by ItsKoga ❤")
            return await ctx.response.send_message(embed=embed, ephemeral=True)

# Ende (20:00 Uhr)
#        if time.tm_hour < 6 or time.tm_hour > 21:
#            embed = discord.Embed(title="Fehler", description="Der osterhase geht nun bis zum nächsten Jahr schlafen!\nDas Event ist nun zu Ende!", color=discord.Color.red())
#            embed.set_footer(text=f"Made by ItsKoga ❤")
#            return await ctx.response.send_message(embed=embed, ephemeral=True)
        
# Start 6:00 Uhr Aktuell nach 15 Uhr
#        if time.tm_hour < 6 or time.tm_hour > 15:
#            embed = discord.Embed(title="Fehler", description="Der osterhase schläft noch!\nDas Event startet um 6:00 Uhr!", color=discord.Color.red())
#            embed.set_footer(text=f"Made by ItsKoga ❤")
#            return await ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Fehler", description="An dem Oster-event können nur verifizierte User teilnehmen! Du kannst dich in <#665566988319326275> mit /verify verifizieren!", color=discord.Color.red())
            embed.set_footer(text=f"Made by ItsKoga ❤")
            return await ctx.response.send_message(embed=embed, ephemeral=True)
        
    @commands.Cog.listener()
    async def on_application_command_completion(self, ctx):
        if ctx.command.name == "collect":
            await asyncio.sleep(120)
            embed = discord.Embed(title="Du kannst wieder /collect ausführen!", description="Es ist zwei Minuten her, seitdem du Punkte für das Oster-Event gesammelt hast.\n\
Führe jetzt wieder /collect im Channel <#1362812143992312000> aus!\n\n\
Du möchtest keine Benachrichtigungen mehr erhalten? Dann deaktiviere den Ping einfach mit dem /notify Befehl.", color=discord.Color.random())
            embed.set_footer(text=f"Made by ItsKoga ❤")
            if system.Get.notifications(ctx.author.id):
                try:
                    await ctx.author.send(embed=embed)
                except discord.Forbidden:
                    log(f"{ctx.author.name} hat DMs deaktiviert!", "ERROR")


    @slash_command(name="collect", description="Geh auf Eiersuche", guild_only=True)
    @is_day()
    @is_verified()
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def collect(self, ctx, location: Option(str, "Wo willst du suchen", choices=["1", "2", "3", "4", "5"], required=False)=None): # type: ignore
        log(f"{ctx.author.name} hat nach Eiern gesucht!", "USER_ACTION")
        await ctx.defer()
        profile = system.Get.user(ctx.author.id)
        embed = discord.Embed(title="Eiersuche", description="Wo willst du suchen", color=0xec6726)
        #embed.set_image(url="https://i.imgur.com/AsSh0xY.png") alt
        embed.set_image(url="https://i.imgur.com/b7u3qAL.png")
        embed.set_footer(text=f"Made by ItsKoga ❤")
        log("/collect : Embed wurde erstellt!", "SYSTEM")

        rabbit_foot = system.Get.rabbit_foot_amount(ctx.author.id)
        while True:
            locations = {}
            for loc in ("1", "2", "3", "4", "5"):
                locations[loc] = system.Gen.nest(loc, ctx, rabbit_foot)

            empty = 0
            for nest in locations:
                if locations[nest].type == "empty":
                    empty += 1
            if empty <= 2:
                break
            
        log("/collect : Nester wurden generiert!", "SYSTEM")


        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = (ctx.author.id, False)
                self.timeout = 60

            async def on_timeout(self):
                if self.value[1] == False:
                    embed = discord.Embed(title="Eiersuche", description="Du hast zu lange gebraucht um ein <:Eier_Nest:1221556705490636880> auszuwählen!", color=discord.Color.red())
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    await self.message.edit(embed=embed, view=None)

            async def show_nest(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value[0]:
                    return await interaction.response.send_message("Du kannst nicht für jemand anderen ein Nest auswählen!", ephemeral=True)
                await interaction.message.edit(view=None)
                embed = discord.Embed(title="Eiersuche", description=("Du hattest eine Hasenpfote, aus diesem Grund wurden alle Eier und Hasenpfoten verdoppelt.\n\n" if system.Get.rabbit_foot_amount(ctx.author.id) else "")+f"**{button.label}.<:Eier_Nest:1221556705490636880>** (Deine Suche: "+(locations[button.label].type if locations[button.label].type != "empty" else "leer")+f"):\n{system.Translate.nest(locations[button.label])}", color=0xec6726)
                for loc in locations:
                    if loc != button.label:
                        embed.add_field(name=f"{loc}.<:Eier_Nest:1221556705490636880> "+(f" ({locations[loc].type})" if locations[loc].type != 'empty' else ' (leer)'), value=system.Translate.nest(locations[loc]), inline=True)
                    else:
                        rewards = locations[loc]
                        system.Update.stats_location(loc)

                embed.set_footer(text=f"Made by ItsKoga ❤")

                await interaction.message.edit(embed=embed)

                log(f"{ctx.author.name} hat {rewards.schokoei} Schokoeier, {rewards.gekochtesEi} gekochte Hühnereier, {rewards.ungekochtesEi} ungekochte Hühnereier, {rewards.egg_talisman} Eier Talisman und {rewards.rabbit_foot_count} Hasenpfoten gefunden!")

                if system.Get.rabbit_foot_amount(self.value[0])!= 0:
                    system.Update.user_remove_one_rabbit_foot_count(self.value[0])

                system.Add.multiple_eggs(self.value[0], "Schokoei", rewards.schokoei)
                log(f"/collect : {ctx.author.name} hat {rewards.schokoei} Schokoeier erhalten!", "SUCCESS")
                system.Add.multiple_eggs(self.value[0], "gekochtes Hühnerei", rewards.gekochtesEi)
                log(f"/collect : {ctx.author.name} hat {rewards.gekochtesEi} gekochte Hühnereier erhalten!", "SUCCESS")
                system.Add.multiple_eggs(self.value[0], "ungekochtes Hühnerei", rewards.ungekochtesEi)
                log(f"/collect : {ctx.author.name} hat {rewards.ungekochtesEi} ungekochte Hühnereier erhalten!", "SUCCESS")

                if rewards.egg_talisman:
                    system.Update.user_egg_talisman(self.value[0], 1)
                    log(f"/collect : {ctx.author.name} hat einen Eier Talisman erhalten!", "SUCCESS")
                for i in range(rewards.rabbit_foot_count):
                    system.Update.user_add_one_rabbit_foot_count(self.value[0])
                    log(f"/collect : {ctx.author.name} hat eine Hasenpfote erhalten!", "SUCCESS")
                
                if rewards.schokoei or rewards.gekochtesEi or rewards.ungekochtesEi:
                    system.Update.stats_add_nests_found()
                    system.Update.user_add_found_nests(self.value[0])

                log(f"{ctx.author.name} wurden die Belohnungen hinzugefügt!", "SUCCESS")
                system.Get.points(self.value[0])
                system.Update.user_add_collect(self.value[0])
                self.value = (self.value[0], True)

            @discord.ui.button(label="1", style=discord.ButtonStyle.gray)
            async def one(self, button: discord.ui.Button, interaction: discord.Interaction):
                await self.show_nest(button, interaction)

            @discord.ui.button(label="2", style=discord.ButtonStyle.gray)
            async def two(self, button: discord.ui.Button, interaction: discord.Interaction):
                await self.show_nest(button, interaction)

            @discord.ui.button(label="3", style=discord.ButtonStyle.gray)
            async def three(self, button: discord.ui.Button, interaction: discord.Interaction):
                await self.show_nest(button, interaction)

            @discord.ui.button(label="4", style=discord.ButtonStyle.gray)
            async def four(self, button: discord.ui.Button, interaction: discord.Interaction):
                await self.show_nest(button, interaction)

            @discord.ui.button(label="5", style=discord.ButtonStyle.gray)
            async def five(self, button: discord.ui.Button, interaction: discord.Interaction):
                await self.show_nest(button, interaction)

        if location == None:
            log(f"{ctx.author.name} hat keine Vorwahl getroffen!", "SYSTEM")
            view = View()
            log("/collect : View wurde erstellt!", "SYSTEM")

            await ctx.followup.send(ctx.author.mention, embed=embed, view=view)
            log("/collect : Embed wurde gesendet!", "SYSTEM")

        else:
            log(f"/collect : {ctx.author.name} hat in der Vorwahl {location} ausgewählt!", "SYSTEM") 
            embed = discord.Embed(title="Eiersuche", description=("Du hattest eine Hasenpfote, aus diesem Grund wurden alle Eier und Hasenpfoten verdoppelt.\n\n" if system.Get.rabbit_foot_amount(ctx.author.id) else "")+f"**{location}.<:Eier_Nest:1221556705490636880>** (Deine Suche: "+(locations[location].type if locations[location].type != "empty" else "leer")+f"):\n{system.Translate.nest(locations[location])}", color=0xec6726)
            log("/collect : Embed wurde erstellt!", "SYSTEM")
            for loc in locations:
                if loc != location:
                    embed.add_field(name=f"{loc}.<:Eier_Nest:1221556705490636880> "+(f" ({locations[loc].type})" if locations[loc].type != 'empty' else ' (leer)'), value=system.Translate.nest(locations[loc]), inline=True)
                else:
                    rewards = locations[loc]
                    system.Update.stats_location(loc)
            log("/collect : Nester wurden eingetragen!", "SYSTEM")
            embed.set_footer(text=f"Made by ItsKoga ❤")

            await ctx.followup.send(ctx.author.mention, embed=embed)
            log("/collect : Embed wurde gesendet!", "SYSTEM")

            if system.Get.rabbit_foot_amount(ctx.author.id)!= 0:
                system.Update.user_remove_one_rabbit_foot_count(ctx.author.id)

            log(f"{ctx.author.name} hat {rewards.schokoei} Schokoeier, {rewards.gekochtesEi} gekochte Hühnereier, {rewards.ungekochtesEi} ungekochte Hühnereier, {rewards.egg_talisman} Eier Talisman und {rewards.rabbit_foot_count} Hasenpfoten gefunden!")

            system.Add.multiple_eggs(ctx.author.id, "Schokoei", rewards.schokoei)
            log(f"/collect : {ctx.author.name} hat {rewards.schokoei} Schokoeier erhalten!", "SUCCESS")
            system.Add.multiple_eggs(ctx.author.id, "gekochtes Hühnerei", rewards.gekochtesEi)
            log(f"/collect : {ctx.author.name} hat {rewards.gekochtesEi} gekochte Hühnereier erhalten!", "SUCCESS")
            system.Add.multiple_eggs(ctx.author.id, "ungekochtes Hühnerei", rewards.ungekochtesEi)
            log(f"/collect : {ctx.author.name} hat {rewards.ungekochtesEi} ungekochte Hühnereier erhalten!", "SUCCESS")

            if rewards.egg_talisman:
                system.Update.user_egg_talisman(ctx.author.id, 1)
                log(f"/collect : {ctx.author.name} hat einen Eier Talisman erhalten!", "SUCCESS")
            for i in range(rewards.rabbit_foot_count):
                system.Update.user_add_one_rabbit_foot_count(ctx.author.id)
                log(f"/collect : {ctx.author.name} hat eine Hasenpfote erhalten!", "SUCCESS")

            if rewards.schokoei or rewards.gekochtesEi or rewards.ungekochtesEi:
                system.Update.stats_add_nests_found()
                system.Update.user_add_found_nests(ctx.author.id)

            log(f"{ctx.author.name} wurden die Belohnungen hinzugefügt!", "SUCCESS")
            system.Get.points(ctx.author.id)
            system.Update.user_add_collect(ctx.author.id)


        

    @slash_command(name="throw", description="Wirf ein Ei auf jemanden", guild_only=True)
    @is_day()
    async def throw(self, ctx, user: discord.User):
        if ctx.author.id == user.id:
            return await ctx.response.send_message("Du kannst nicht auf dich selbst werfen!", ephemeral=True)
        if user.bot:
            return await ctx.response.send_message("Du kannst nicht auf Bots werfen!", ephemeral=True)
        check = system.Get.egg_check(ctx.author.id, "ungekochtes Hühnerei")
        if check == False:
            return await ctx.response.send_message("Du hast keine :egg:!", ephemeral=True)
        if system.Get.type_eggs(user.id, "Schokoei") == []:
            return await ctx.response.send_message("Dieser User hat keine <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if system.Get.user(user.id).last_hit > tm.time()-300:
            return await ctx.response.send_message(f"Dieser User wurde in den letzten 5 Minuten bereits abgeworfen! Versuche es <t:{system.Get.user(user.id).last_hit+300}:R> erneut.", ephemeral=True)
        log(f"{ctx.author.name} hat ein Ei auf {user.name} geworfen!", "USER_ACTION")
        
        success = random.choice([0, 1])
        system.Add.throw(ctx.author.id, user.id, success)
        if success == 0:
            embed = discord.Embed(title="Eierwurf", description=f"Du hast ein :egg: auf {user.mention} geworfen, aber es ist daneben gegangen!", color=discord.Color.red())

        else:
            points = system.Get.points(user.id)
            percent = system.Get.throw_percent(points)
            reward = int(points/100*percent)

            eggs = system.Get.type_eggs(user.id, "Schokoei")
            embed = None
            for i in range(reward):
                if eggs[i]:
                    system.Update.egg_owner(eggs[i].id, ctx.author.id)
                    log(f"/throw : {ctx.author.name} hat ein {eggs[i].type} von {user.name} erhalten!", "SUCCESS")
                else:
                    reward = i 
                    embed = discord.Embed(title="Eierwurf", description=f"Du hast ein :egg: auf {user.mention} geworfen und getroffen! Du hast {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten! Der rest war bei der Oma.", color=discord.Color.green())
                    break
            
            system.Update.user_last_hit(user.id)

            if not embed:
                embed = discord.Embed(title="Eierwurf", description=f"Du hast ein :egg: auf {user.mention} geworfen und getroffen! Du hast {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten!", color=discord.Color.green())
                
        system.Delete.egg(check.id)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        await ctx.response.send_message(user.mention,embed=embed)
        system.Get.points(ctx.author.id)
        

    @slash_command(name="fight", description="Fordere jemanden zum Kampf heraus", guild_only=True)
    @is_day()
    async def fight(self, ctx, user: discord.User, bet: int):
        if ctx.author.id == user.id:
            return await ctx.response.send_message("Du kannst nicht gegen dich selbst kämpfen!", ephemeral=True)
        if user.bot:
            return await ctx.response.send_message("Du kannst nicht gegen Bots kämpfen!", ephemeral=True)
        if bet < 1:
            return await ctx.response.send_message("Du musst mindestens 1 <:Schoko_Ei:1221556659030196284> setzen!", ephemeral=True)
        if bet > 25:
            return await ctx.response.send_message("Du kannst maximal 25 <:Schoko_Ei:1221556659030196284> setzen!", ephemeral=True)
        if len(system.Get.type_eggs(ctx.author.id, "Schokoei")) < bet:
            return await ctx.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if len(system.Get.type_eggs(user.id, "Schokoei")) < bet:
            return await ctx.response.send_message("Dein Gegner hat nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if system.Get.egg_check(ctx.author.id, "gekochtes Hühnerei") == False:
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        if system.Get.egg_check(user.id, "gekochtes Hühnerei") == False:
            return await ctx.response.send_message("Dein Gegner hat kein <:osterei:962802014226640996>!", ephemeral=True)
        log(f"{ctx.author.name} hat {user.name} zum Kampf herausgefordert!", "USER_ACTION")

        embed = discord.Embed(title="Kampf Anfrage", description=f"{ctx.author.mention} hat dich zu einem Kampf um {bet}x <:Schoko_Ei:1221556659030196284> herausgefordert! Möchtest du annehmen?", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = user.id

            async def on_timeout(self):
                if self.value != True:
                    self.disable_all_items()
                    await self.message.edit(view=self)
                    await ctx.response.send_message("Kampf Anfrage wurde nicht angenommen!", ephemeral=True)

            @discord.ui.button(label="Annehmen", style=discord.ButtonStyle.success)
            async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Du kannst nicht für jemand anderen antworten!", ephemeral=True)
                self.value = True
                self.disable_all_items()
                await interaction.message.edit(view=self)

                winner = random.choice([ctx.author.id, user.id])
                looser = ctx.author.id if winner == user.id else user.id
                embed = discord.Embed(title="Kampf", description=f"{ctx.author.mention} und {user.mention} kämpfen!", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await interaction.response.send_message(embed=embed)

                system.Add.solo_fight(ctx.author.id, user.id, bet, winner)
                eggs = system.Get.type_eggs(looser, "Schokoei")

                if len(eggs) < bet:
                    embed = discord.Embed(title="Error", description=f"{ctx.author.mention} hat nicht mehr genug <:Schoko_Ei:1221556659030196284>!", color=discord.Color.red())
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    return await interaction.original_response.edit_message(embed=embed)
                
                for i in range(bet):
                    system.Update.egg_owner(eggs[i].id, winner)
                    log(f"/fight : {winner} hat ein {eggs[i].type} von {looser} erhalten!", "SUCCESS")
                system.Delete.egg(system.Get.egg_check(looser, "gekochtes Hühnerei").id)

                await asyncio.sleep(4)
                embed = discord.Embed(title="Kampf", description=system.Gen.solo_fight_text(winner, looser, bet, [ctx.author.id, user.id]), color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                msg = await interaction.original_response()
                msg = await msg.reply(embed=embed)
                        
                await asyncio.sleep(4)
                embed = discord.Embed(title="Kampf", description=f"<@{winner}> hat den Kampf gewonnen!\n\
Und erhält {bet}x <:Schoko_Ei:1221556659030196284> von <@{looser}>.", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await msg.reply(embed=embed)
            
            
            @discord.ui.button(label="Ablehnen", style=discord.ButtonStyle.danger)
            async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id != self.value:
                    return await interaction.response.send_message("Du kannst nicht für jemand anderen antworten!", ephemeral=True)
                self.value = False
                self.disable_all_items()
                await interaction.message.edit(view=self)
                await interaction.response.send_message("Kampf Anfrage wurde abgelehnt!",)

        view = View()
        await ctx.response.send_message(user.mention, embed=embed, view=view)
        system.Get.points(ctx.author.id)
        system.Get.points(user.id)

    
    @slash_command(name="group_fight", description="Starte einen Gruppenkampf", guild_only=True)
    @is_day()
    async def group_fight(self, ctx, bet: int):
        global group_fight_running
        if ctx.author.id == os.getenv("OWNER_ID") and bet == 4444:
            group_fight_running = False
            return await ctx.response.send_message("Gruppenkampf wurde zurückgesetzt!", ephemeral=True)
        if group_fight_running == True:
            log(f"{ctx.author.name} hat versucht einen Gruppenkampf zu starten, obwohl bereits einer läuft!", "ERROR")
            return await ctx.response.send_message("Es läuft bereits ein Gruppenkampf!", ephemeral=True)
        if bet < 4:
            log(f"{ctx.author.name} hat versucht einen Gruppenkampf zu starten, aber zu wenig <:Schoko_Ei:1221556659030196284> gesetzt!", "ERROR")
            return await ctx.response.send_message("Du musst mindestens 4 <:Schoko_Ei:1221556659030196284> setzen!", ephemeral=True)
        if bet > 25:
            log(f"{ctx.author.name} hat versucht einen Gruppenkampf zu starten, aber zu viele <:Schoko_Ei:1221556659030196284> gesetzt!", "ERROR")
            return await ctx.response.send_message("Du kannst maximal 25 <:Schoko_Ei:1221556659030196284> setzen!", ephemeral=True)
        if len(system.Get.type_eggs(ctx.author.id, "Schokoei")) < bet:
            log(f"{ctx.author.name} hat versucht einen Gruppenkampf zu starten, aber nicht genug <:Schoko_Ei:1221556659030196284>!", "ERROR")
            return await ctx.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if system.Get.egg_check(ctx.author.id, "gekochtes Hühnerei") == False:
            log(f"{ctx.author.name} hat versucht einen Gruppenkampf zu starten, aber kein <:osterei:962802014226640996>!", "ERROR")
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        system.Update.last_fight(ctx.author.id)
        group_fight_running = True
        log(f"{ctx.author.name} hat einen Gruppenkampf gestartet!", "USER_ACTION")

        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = [ctx.author.id]
                self.timeout = 60

            async def on_timeout(self):
                await self.message.edit(view=None)
                if bet*len(self.value) > 500:
                    return await self.message.reply("Das Maximum an <:Schoko_Ei:1221556659030196284> für einen Gruppenkampf beträgt 500x <:Schoko_Ei:1221556659030196284>!")
                
                for user in self.value:
                    check = system.Get.type_eggs(user, "gekochtes Hühnerei")
                    if check == []:
                        self.value.remove(user)
                        log(f"/group_fight : {user} hat kein gekochtes Hühnerei!", "ERROR")
                    else:
                        system.Delete.egg(check[0].id)
                        log(f"/group_fight : {user} sein gekochtes Hühnerei wurde entfernt!", "SYSTEM")
                global group_fight_running

                if len(self.value) < 4:
                    group_fight_running = False
                    for user in self.value:
                        system.Update.reset_last_fight(user)
                        log(f"/group_fight : {user} hat sein gekochtes Hühnerei zurück erhalten!", "SYSTEM")
                    return await self.message.reply("Nicht genug Spieler für den Gruppenkampf!")
                
                string = "\n".join([f"- <@{user}>" for user in self.value])
                embed = discord.Embed(title="Gruppenkampf", description=f"Der Gruppenkampf beginnt!\n**Teilnehmer:({len(self.value)}/4)** \n{string}", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                log(f"/group_fight : Gruppenkampf beginnt mit {len(self.value)} Spielern!", "SYSTEM")
                msg = await self.message.reply(embed=embed)

                eggs = []
                for user in self.value:
                    user_eggs = system.Get.type_eggs(user, "Schokoei")
                    for i in range(bet):
                        eggs.append(user_eggs[i])
                log(f"/group_fight : Eggs für Belohnungen wurden geladen!", "SYSTEM")

                system.Add.user(111111111111111111)
                for egg in eggs:
                    system.Update.egg_owner(egg.id, 111111111111111111)
                log(f"/group_fight : Eggs wurden versteckt!", "SYSTEM")
                                                                    
                await asyncio.sleep(5)

                egg_amount = len(eggs)
                rewards = [int(egg_amount*0.6), int(egg_amount*0.25), int(egg_amount*0.15)]
                if sum(rewards) < egg_amount:
                    rewards[0] += sum(rewards) - egg_amount
                if sum(rewards) > bet*len(self.value):
                    rewards[0] += sum(rewards) - egg_amount
                log(f"/group_fight : Belohnungen wurden berechnet! ({rewards})", "SYSTEM")

                top = []
                while len(self.value) > 2:
                    player1 = random.choice(self.value)
                    player2 = random.choice([player for player in self.value if player != player1])
                    log(f"/group_fight : {player1} und {player2} kämpfen!", "SYSTEM")

                    winner = random.choice([player1, player2])
                    looser = player1 if winner == player2 else player2
                    log(f"/group_fight : {winner} hat den Kampf gegen {looser} gewonnen!", "SYSTEM")
        
                    top.append(looser)

                    embed = discord.Embed(title="Gruppenkampf", description=f"<@{player1}> und <@{player2}> kämpfen!", color=0xec6726)
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    msg = await msg.reply(embed=embed)
                    log(f"/group_fight : Embed wurde erstellt und gesendet!", "SYSTEM")

                    await asyncio.sleep(5)
                    
                    embed = discord.Embed(title="Gruppenkampf", description=system.Gen.group_fight_text([player1, player2]), color=0xec6726)
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    msg = await msg.reply(embed=embed)
                    log(f"/group_fight : Embed wurde erstellt und gesendet!", "SYSTEM")

                    await asyncio.sleep(5)

                    embed = discord.Embed(title="Gruppenkampf", description=f"<@{winner}> hat den Kampf gewonnen!\n\
<@{looser}> ist auf Platz {len(self.value)} ausgeschieden!", color=0xec6726)
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    msg = await msg.reply(embed=embed)
                    log(f"/group_fight : Embed wurde erstellt und gesendet!", "SYSTEM")

                    self.value.remove(looser)
                    log(f"/group_fight : {looser} wurde aus dem Kampf entfernt!", "SYSTEM")

                    await asyncio.sleep(5)

                embed = discord.Embed(title="Gruppenkampf", description=f"<@{self.value[0]}> und <@{self.value[1]}> ditschen was das Zeug hält!, wer wird sich den ersten Platz holen?", color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                msg = await msg.reply(embed=embed)
                log(f"/group_fight : Der letzte Kampf beginnt!", "SYSTEM")

                await asyncio.sleep(5)

                winner = random.choice(self.value)
                looser = self.value[0] if winner == self.value[1] else self.value[1]
                system.Delete.egg(system.Get.egg_check(looser, "gekochtes Hühnerei").id)
                log(f"/group_fight : {winner} hat den Gruppenkampf gewonnen!", "SYSTEM")

                top.append(looser)
                top.reverse()
                self.value.remove(looser)

                embed = discord.Embed(title="Gruppenkampf", description=system.Gen.group_fight_loose_text(looser), color=0xec6726)
                embed.set_footer(text=f"Made by ItsKoga ❤")
                msg = await msg.reply(embed=embed)
                log(f"/group_fight : Alle Kämpfe sind beendet!", "SYSTEM")

                await asyncio.sleep(5)
                
                embed = discord.Embed(title="Gruppenkampf", description=system.Gen.group_fight_loose_text(looser))

                embed.set_footer(text=f"Made by ItsKoga ❤")
                msg = await msg.reply(embed=embed)
                log(f"/group_fight : {self.value[0]} hat den Gruppenkampf gewonnen!", "SYSTEM")

                participants = [self.value[0]] + top

                for i in range(len(rewards)):
                    for j in range(rewards[i]):
                        system.Update.egg_owner(eggs[0].id, participants[i])
                        log(f"/group_fight : {participants[i]} hat ein {eggs[0].type}({eggs[0].id}) erhalten!", "SUCCESS")
                        eggs.remove(eggs[0])
                    system.Get.points(participants[i])
                    log(f"/group_fight : {participants[i]} hat seine Eggs erhalten!", "SYSTEM")

                embed = discord.Embed(title="Gruppenkampf", description=f"<@{self.value[0]}> hat den Gruppenkampf gewonnen!\n\n\
<@{self.value[0]}> erhält {rewards[0]}x <:Schoko_Ei:1221556659030196284>!\n\
<@{top[0]}> erhält {rewards[1]}x <:Schoko_Ei:1221556659030196284>!\n\
<@{top[1]}> erhält {rewards[2]}x <:Schoko_Ei:1221556659030196284>!", color=discord.Color.green())
                embed.set_footer(text=f"Made by ItsKoga ❤")
                await msg.edit(embed=embed)
                group_fight_running = False
                log(f"/group_fight : Der Gruppenkampf ist beendet!", "SYSTEM")


            @discord.ui.button(label="Beitreten", style=discord.ButtonStyle.green)
            async def join(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id in self.value:
                    return await interaction.response.send_message("Du bist bereits beigetreten!", ephemeral=True)
                if len(system.Get.type_eggs(interaction.user.id, "Schokoei")) < bet:
                    return await interaction.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
                if system.Get.egg_check(interaction.user.id, "gekochtes Hühnerei") == False:
                    return await interaction.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
                self.value.append(interaction.user.id)
                await interaction.response.send_message("Du bist dem Gruppenkampf beigetreten!", ephemeral=True)
                system.Update.last_fight(interaction.user.id)
                log(f"/group_fight : {interaction.user.name} ist dem Gruppenkampf beigetreten!", "USER_ACTION")

                self.message.embeds[0].set_field_at(0, name=f"Teilnehmer({len(self.value)}/4)", value="\n".join([f"- <@{user}>" for user in self.value]), inline=False)
                await self.message.edit(embed=self.message.embeds[0])


        embed = discord.Embed(title="Gruppenkampf", description=f"{ctx.author.mention} hat einen Gruppenkampf gestartet! Möchtest du beitreten? Der Kampf beginnt <t:{int(tm.time()+80)}:R>.\n\
Gewettet wird um {bet}x <:Schoko_Ei:1221556659030196284>.", color=0xec6726)
        embed.add_field(name="Teilnehmer(1/4)", value=f"- <@{ctx.author.id}>", inline=False)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        log(f"/group_fight : Embed wurde erstellt!", "SYSTEM")
        view = View()
        log(f"/group_fight : View wurde erstellt!", "SYSTEM")
        await ctx.response.send_message(embed=embed, view=view)
        log(f"/group_fight : Embed wurde gesendet!", "SYSTEM")



    @slash_command(name="bake", description="Backe ein Kuchen", guild_only=True)
    @is_day()
    async def bake(self, ctx):
        log(f"{ctx.author.name} hat /bake ausgeführt!", "USER_ACTION")
        check = system.Get.bake_check(ctx.author.id)
        if check == False:
            amount_uncooked = len(system.Get.type_eggs_not_rotten(ctx.author.id, "ungekochtes Hühnerei"))
            amount_chocolate = len(system.Get.type_eggs(ctx.author.id, "Schokoei"))
            embed = discord.Embed(title="Kuchen backen", description="Du hast nicht alle Zutaten, daher kann dir deine Oma nicht helfen!", color=discord.Color.red())
            embed.add_field(name="Zutaten", value=f"3x :egg: (Du besitzt: {amount_uncooked})\n10x <:Schoko_Ei:1221556659030196284> (Du besitzt: {amount_chocolate})", inline=False)
            embed.set_footer(text=f"Made by ItsKoga ❤")
            return await ctx.response.send_message(embed=embed, ephemeral=True)
        log(f"{ctx.author.name} hat ein kuchen gebacken!", "USER_ACTION")
        system.Add.cake(ctx.author.id)
        embed = discord.Embed(title="Kuchen backen", description="Deine Oma hat dir geholfen einen :cake: zu backen! Da niemand von einer Oma klaut sind deine Punkte sicher!", color=discord.Color.green())
        await ctx.response.send_message(embed=embed, ephemeral=True)
        system.Get.points(ctx.author.id)
        

    @slash_command(name="talisman", description="Zeigt dir deinen Eier Talisman", guild_only=True)
    @is_day()
    async def talisman(self, ctx, richtung: Option(str, "Wähle welche Chance dein Talisman erhöhen soll", choices=["Rohe Eier", "Ostereier"])): # type: ignore
        profile = system.Get.user(ctx.author.id)
        if profile.egg_talisman == 0:
            return await ctx.response.send_message("Du hast noch keinen Eier Talisman!", ephemeral=True)
        if richtung == "Rohe Eier":
            system.Update.user_egg_talisman(ctx.author.id, 2)
            await ctx.response.send_message("Dein Eier Talisman erhöht jetzt die Chance auf :egg:!", ephemeral=True)
        else:
            system.Update.user_egg_talisman(ctx.author.id, 1)
            await ctx.response.send_message("Dein Eier Talisman erhöht jetzt die Chance auf <:osterei:962802014226640996>!", ephemeral=True)
        log(f"{ctx.author.name} hat seinen Talisman geändert!", "USER_ACTION")


    @slash_command(name="lose", description="Tausche ein Gekochtes Ei gegen ein Los", guild_only=True)
    @is_day()
    async def lose(self, ctx, amount: int):
        if amount < 1:
            return await ctx.response.send_message("Du musst mindestens 1 <:osterei:962802014226640996> eintauschen!", ephemeral=True)
        if amount > 25:
            return await ctx.response.send_message("Du kannst maximal 25 <:osterei:962802014226640996> auf einmal eintauschen!", ephemeral=True)
        if system.Get.egg_check(ctx.author.id, "gekochtes Hühnerei") == False:
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        if len(system.Get.type_eggs_not_rotten(ctx.author.id, "gekochtes Hühnerei")) < amount:
            return await ctx.response.send_message("Du hast nicht genug <:osterei:962802014226640996>!", ephemeral=True)
        log(f"{ctx.author.name} hat /lose ausgeführt!", "USER_ACTION")
        system.Add.lose(ctx.author.id, amount)
        embed = discord.Embed(title="Verloren", description=f"Du hast {amount}x <:osterei:962802014226640996> eingetauscht!", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        await ctx.response.send_message(embed=embed, ephemeral=True)
            

        
def setup(bot):
    bot.add_cog(Game(bot))
