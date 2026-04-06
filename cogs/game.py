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
from datetime import datetime
from zoneinfo import ZoneInfo
import discord

log = log_helper.create("Game")
group_fight_running = False
EVENT_TIMEZONE = os.getenv("EVENT_TIMEZONE", "Europe/Berlin")


def get_event_hour() -> int:
    try:
        return datetime.now(ZoneInfo(EVENT_TIMEZONE)).hour
    except Exception:
        # Fallback to system local time if timezone config is invalid.
        return tm.localtime().tm_hour



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


# Normal (06:00 - 00:00 Uhr)
#def is_day():
#    def day(ctx):
#        hour = get_event_hour()
#        if hour < 6 or hour > 23:
#            return False
#        return True
#    return commands.check(day)

# Ende (06:00 - 22:00 Uhr)
def is_day():
    def day(ctx):
        time = tm.localtime()
        if time.tm_hour < 6 or time.tm_hour > 21:
            return False
        return True
    return commands.check(day)

# Start (06:00 - 16:00 Uhr)
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

        hour = get_event_hour()
# Normal (22:00 Uhr)
    #        if hour < 6 or hour > 23:
#            embed = discord.Embed(title="Fehler", description="Der Osterhase versteckt zwischen 0:00 und 6:00 Uhr neue Eier, aus diesem Grund hat deine Oma dich ins Bett geschickt!", color=discord.Color.red())
#            embed.set_footer(text=f"Made by ItsKoga ❤")
#            return await ctx.response.send_message(embed=embed, ephemeral=True)

# Ende (20:00 Uhr)
        if hour < 6 or hour > 21:
            embed = discord.Embed(title="Fehler", description="Der osterhase geht nun bis zum nächsten Jahr schlafen!\nDas Event ist nun zu Ende!", color=discord.Color.red())
            embed.set_footer(text=f"Made by ItsKoga ❤")
            return await ctx.response.send_message(embed=embed, ephemeral=True)
        
# Start 6:00 Uhr Aktuell nach 15 Uhr
    #        if hour < 6 or hour > 15:
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
Führe jetzt wieder /collect im Channel <#1489517152300957766> aus!\n\n\
Du möchtest keine Benachrichtigungen mehr erhalten? Dann deaktiviere den Ping einfach mit dem /notify Befehl.", color=discord.Color.random())
            embed.set_footer(text=f"Made by ItsKoga ❤")
            if await system.Get.notifications(ctx.author.id):
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
        profile = await system.Get.user(ctx.author.id)
        embed = discord.Embed(title="Eiersuche", description="Wo willst du suchen", color=0xec6726)
        embed.set_image(url=random.choice(["https://i.imgur.com/b7u3qAL.png", "https://i.imgur.com/AsSh0xY.png"]))
        embed.set_footer(text=f"Made by ItsKoga ❤")
        #log("/collect : Embed wurde erstellt!", "DEBUG")

        rabbit_foot = await system.Get.rabbit_foot_amount(ctx.author.id)
        while True:
            locations = {}
            for loc in ("1", "2", "3", "4", "5"):
                locations[loc] = await system.Gen.nest(loc, ctx, rabbit_foot)

            empty = 0
            for nest in locations:
                if locations[nest].type == "empty":
                    empty += 1
            if empty <= 2:
                break
            
        #log("/collect : Nester wurden generiert!", "DEBUG")


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
                embed = discord.Embed(title="Eiersuche", description=("Du hattest eine Hasenpfote, aus diesem Grund wurden alle Eier und Hasenpfoten verdoppelt.\n\n" if await system.Get.rabbit_foot_amount(ctx.author.id) else "")+f"**{button.label}.<:Eier_Nest:1221556705490636880>** (Deine Suche: "+(locations[button.label].type if locations[button.label].type != "empty" else "leer")+f"):\n{await system.Translate.nest(locations[button.label])}", color=0xec6726)
                for loc in locations:
                    if loc != button.label:
                        embed.add_field(name=f"{loc}.<:Eier_Nest:1221556705490636880> "+(f" ({locations[loc].type})" if locations[loc].type != 'empty' else ' (leer)'), value=await system.Translate.nest(locations[loc]), inline=True)
                    else:
                        rewards = locations[loc]
                        await system.Update.stats_location(loc)

                embed.set_footer(text=f"Made by ItsKoga ❤")

                await interaction.message.edit(embed=embed)

                log(f"{ctx.author.name} hat {rewards.schokoei} Schokoeier, {rewards.gekochtesEi} gekochte Hühnereier, {rewards.ungekochtesEi} ungekochte Hühnereier, {rewards.egg_talisman} Eier Talisman und {rewards.rabbit_foot_count} Hasenpfoten gefunden!")

                if await system.Get.rabbit_foot_amount(self.value[0])!= 0:
                    await system.Update.user_remove_one_rabbit_foot_count(self.value[0])

                await system.Add.multiple_eggs(self.value[0], "Schokoei", rewards.schokoei)
                #log(f"/collect : {ctx.author.name} hat {rewards.schokoei} Schokoeier erhalten!", "DEBUG")
                await system.Add.multiple_eggs(self.value[0], "cooked", rewards.gekochtesEi)
                #log(f"/collect : {ctx.author.name} hat {rewards.gekochtesEi} gekochte Hühnereier erhalten!", "DEBUG")
                await system.Add.multiple_eggs(self.value[0], "uncooked", rewards.ungekochtesEi)
                #log(f"/collect : {ctx.author.name} hat {rewards.ungekochtesEi} ungekochte Hühnereier erhalten!", "DEBUG")

                if rewards.egg_talisman:
                    await system.Update.user_egg_talisman(self.value[0], 1)
                    log(f"/collect : {ctx.author.name} hat einen Eier Talisman erhalten!")
                for i in range(rewards.rabbit_foot_count):
                    await system.Update.user_add_one_rabbit_foot_count(self.value[0])
                    log(f"/collect : {ctx.author.name} hat eine Hasenpfote erhalten!")
                
                if rewards.schokoei or rewards.gekochtesEi or rewards.ungekochtesEi:
                    await system.Update.stats_add_nests_found()
                    await system.Update.user_add_found_nests(self.value[0])

                log(f"{ctx.author.name} wurden die Belohnungen hinzugefügt!", "SUCCESS")
                await system.Get.points(self.value[0])
                await system.Update.user_add_collect(self.value[0])
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
            #log(f"{ctx.author.name} hat keine Vorwahl getroffen!", "DEBUG")
            view = View()
            #log("/collect : View wurde erstellt!", "DEBUG")

            await ctx.response.send_message(ctx.author.mention, embed=embed, view=view)
            #log("/collect : Embed wurde gesendet!", "DEBUG")

        else:
            #log(f"/collect : {ctx.author.name} hat in der Vorwahl {location} ausgewählt!", "DEBUG") 
            embed = discord.Embed(title="Eiersuche", description=("Du hattest eine Hasenpfote, aus diesem Grund wurden alle Eier und Hasenpfoten verdoppelt.\n\n" if await system.Get.rabbit_foot_amount(ctx.author.id) else "")+f"**{location}.<:Eier_Nest:1221556705490636880>** (Deine Suche: "+(locations[location].type if locations[location].type != "empty" else "leer")+f"):\n{await system.Translate.nest(locations[location])}", color=0xec6726)
            #log("/collect : Embed wurde erstellt!", "DEBUG")
            for loc in locations:
                if loc != location:
                    embed.add_field(name=f"{loc}.<:Eier_Nest:1221556705490636880> "+(f" ({locations[loc].type})" if locations[loc].type != 'empty' else ' (leer)'), value=await system.Translate.nest(locations[loc]), inline=True)
                else:
                    rewards = locations[loc]
                    await system.Update.stats_location(loc)
            #log("/collect : Nester wurden eingetragen!", "DEBUG")
            embed.set_footer(text=f"Made by ItsKoga ❤")

            await ctx.response.send_message(ctx.author.mention, embed=embed)
            #log("/collect : Embed wurde gesendet!", "DEBUG")

            if await system.Get.rabbit_foot_amount(ctx.author.id)!= 0:
                await system.Update.user_remove_one_rabbit_foot_count(ctx.author.id)

            log(f"{ctx.author.name} hat {rewards.schokoei} Schokoeier, {rewards.gekochtesEi} gekochte Hühnereier, {rewards.ungekochtesEi} ungekochte Hühnereier, {rewards.egg_talisman} Eier Talisman und {rewards.rabbit_foot_count} Hasenpfoten gefunden!")

            await system.Add.multiple_eggs(ctx.author.id, "Schokoei", rewards.schokoei)
            #log(f"/collect : {ctx.author.name} hat {rewards.schokoei} Schokoeier erhalten!", "DEBUG")
            await system.Add.multiple_eggs(ctx.author.id, "cooked", rewards.gekochtesEi)
            #log(f"/collect : {ctx.author.name} hat {rewards.gekochtesEi} gekochte Hühnereier erhalten!", "DEBUG")
            await system.Add.multiple_eggs(ctx.author.id, "uncooked", rewards.ungekochtesEi)
            #log(f"/collect : {ctx.author.name} hat {rewards.ungekochtesEi} ungekochte Hühnereier erhalten!", "DEBUG")

            if rewards.egg_talisman:
                await   system.Update.user_egg_talisman(ctx.author.id, 1)
                log(f"/collect : {ctx.author.name} hat einen Eier Talisman erhalten!", "SUCCESS")
            for i in range(rewards.rabbit_foot_count):
                await system.Update.user_add_one_rabbit_foot_count(ctx.author.id)
                log(f"/collect : {ctx.author.name} hat eine Hasenpfote erhalten!", "SUCCESS")

            if rewards.schokoei or rewards.gekochtesEi or rewards.ungekochtesEi:
                await system.Update.stats_add_nests_found()
                await system.Update.user_add_found_nests(ctx.author.id)

            log(f"{ctx.author.name} wurden die Belohnungen hinzugefügt!", "SUCCESS")
            await system.Get.points(ctx.author.id)
            await system.Update.user_add_collect(ctx.author.id)


        

    @slash_command(name="throw", description="Wirf ein Ei auf jemanden", guild_only=True)
    @is_day()
    async def throw(self, ctx, user: discord.User):
        if ctx.author.id == user.id:
            return await ctx.response.send_message("Du kannst nicht auf dich selbst werfen!", ephemeral=True)
        if user.bot:
            return await ctx.response.send_message("Du kannst nicht auf Bots werfen!", ephemeral=True)
        check = await system.Get.egg_check(ctx.author.id, "uncooked")
        if check == False:
            return await ctx.response.send_message("Du hast keine :egg:!", ephemeral=True)
        if (await system.Get.user(user.id)).chocolate_eggs == 0:
            return await ctx.response.send_message("Dieser User hat keine <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if (await system.Get.user(user.id)).last_hit > tm.time()-300:
            return await ctx.response.send_message(f"Dieser User wurde in den letzten 5 Minuten bereits abgeworfen! Versuche es <t:{(await system.Get.user(user.id)).last_hit+300}:R> erneut.", ephemeral=True)
        log(f"{ctx.author.name} hat ein Ei auf {user.name} geworfen!", "USER_ACTION")
        
        success = random.choice([0, 1])
        await system.Add.throw(ctx.author.id, user.id, success)
        
        thrower = await system.Get.user(ctx.author.id)
        defender = await system.Get.user(user.id)
        
        if success == 0:
            embed = discord.Embed(title="Eierwurf", description=f"Du hast ein :egg: auf {user.mention} geworfen, aber es ist daneben gegangen!", color=discord.Color.red())

        else:
            points = defender.points
            percent = system.Get.throw_percent(points)
            reward = int(points/100*percent)

            eggs = defender.chocolate_eggs
            embed = None

            if eggs >= reward:
                real_reward = reward
            else:
                real_reward = eggs

            #transfer the eggs
            await system.Transfer.chocolate_eggs(user.id, ctx.author.id, real_reward)


            #log(f"/throw : {ctx.author.name} hat {reward} Schokoeier von {user.name} erhalten!", "DEBUG")
            if real_reward == reward:
                embed = discord.Embed(title="Eierwurf", description=f"Du hast ein :egg: auf {user.mention} geworfen und getroffen! Du hast {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten!", color=discord.Color.green())
            else:
                embed = discord.Embed(title="Eierwurf", description=f"Du hast ein :egg: auf {user.mention} geworfen und getroffen! Du hast {real_reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten! Der rest war bei der Oma.", color=discord.Color.green())
            
            await system.Update.user_last_hit(user.id)

        
        await system.Delete.egg(check.id)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        await ctx.response.send_message(user.mention,embed=embed)
        await system.Get.points(ctx.author.id)
        

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
        if (await system.Get.user(ctx.author.id)).chocolate_eggs < bet:
            return await ctx.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if (await system.Get.user(user.id)).chocolate_eggs < bet:
            return await ctx.response.send_message("Dein Gegner hat nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if await system.Get.egg_check(ctx.author.id, "cooked") == False:
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        if await system.Get.egg_check(user.id, "cooked") == False:
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

                await system.Add.solo_fight(ctx.author.id, user.id, bet, winner)
                eggs = (await system.Get.user(looser)).chocolate_eggs

                if eggs < bet:
                    embed = discord.Embed(title="Error", description=f"{ctx.author.mention} hat nicht mehr genug <:Schoko_Ei:1221556659030196284>!", color=discord.Color.red())
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    return await interaction.original_response.edit_message(embed=embed)
                
                await system.Transfer.chocolate_eggs(looser, winner, bet)
                log(f"/fight : {winner} hat {bet} Schokoeier von {looser} erhalten!", "SUCCESS")
                await system.Delete.egg((await system.Get.egg_check(looser, "cooked")).id)

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
        await system.Get.points(ctx.author.id)
        await system.Get.points(user.id)

    
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
        if (await system.Get.user(ctx.author.id)).chocolate_eggs < bet:
            log(f"{ctx.author.name} hat versucht einen Gruppenkampf zu starten, aber nicht genug <:Schoko_Ei:1221556659030196284>!", "ERROR")
            return await ctx.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
        if await system.Get.egg_check(ctx.author.id, "cooked") == False:
            log(f"{ctx.author.name} hat versucht einen Gruppenkampf zu starten, aber kein <:osterei:962802014226640996>!", "ERROR")
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        await system.Update.last_fight(ctx.author.id)
        group_fight_running = True
        log(f"{ctx.author.name} hat einen Gruppenkampf gestartet!", "USER_ACTION")

        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = [ctx.author.id]
                self.timeout = 60

            async def on_timeout(self):
                global group_fight_running
                try:
                    await self.message.edit(view=None)
                    if bet*len(self.value) > 500:
                        group_fight_running = False
                        return await self.message.reply("Das Maximum an <:Schoko_Ei:1221556659030196284> für einen Gruppenkampf beträgt 500x <:Schoko_Ei:1221556659030196284>!")
                    
                    for user in self.value:
                        check = await system.Get.type_eggs(user, "cooked")
                        if check == []:
                            self.value.remove(user)
                            log(f"/group_fight : {user} hat kein gekochtes Hühnerei!", "ERROR")
                        else:
                            await system.Delete.egg(check[0].id)
                            log(f"/group_fight : {user} sein gekochtes Hühnerei wurde entfernt!", "SYSTEM")

                    if len(self.value) < 3:
                        group_fight_running = False
                        for user in self.value:
                            await system.Update.reset_last_fight(user)
                            log(f"/group_fight : {user} hat sein gekochtes Hühnerei zurück erhalten!", "SYSTEM")
                        return await self.message.reply("Nicht genug Spieler für den Gruppenkampf!")
                    
                    string = "\n".join([f"- <@{user}>" for user in self.value])
                    embed = discord.Embed(title="Gruppenkampf", description=f"Der Gruppenkampf beginnt!\n**Teilnehmer:({len(self.value)}/4)** \n{string}", color=0xec6726)
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    log(f"/group_fight : Gruppenkampf beginnt mit {len(self.value)} Spielern!", "SYSTEM")
                    msg = await self.message.reply(embed=embed)

                    eggs = 0
                    await system.Add.user(111111111111111111)
                    for user in self.value:
                        eggs += bet
                        await system.Transfer.chocolate_eggs(user, 111111111111111111, bet)
                    log(f"/group_fight : Eggs für Belohnungen wurden geladen!", "SYSTEM")
                                                                        
                    await asyncio.sleep(5)

                    egg_amount = eggs
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
                        await system.Transfer.chocolate_eggs(111111111111111111, participants[i], rewards[i])
                        log(f"/group_fight : {rewards[i]} Schokoeier wurden an {participants[i]} übertragen!", "SYSTEM")
                        await system.Get.points(participants[i])

                    embed = discord.Embed(title="Gruppenkampf", description=f"<@{self.value[0]}> hat den Gruppenkampf gewonnen!\n\n\
<@{self.value[0]}> erhält {rewards[0]}x <:Schoko_Ei:1221556659030196284>!\n\
<@{top[0]}> erhält {rewards[1]}x <:Schoko_Ei:1221556659030196284>!\n\
<@{top[1]}> erhält {rewards[2]}x <:Schoko_Ei:1221556659030196284>!", color=discord.Color.green())
                    embed.set_footer(text=f"Made by ItsKoga ❤")
                    await msg.edit(embed=embed)
                    group_fight_running = False
                    log(f"/group_fight : Der Gruppenkampf ist beendet!", "SYSTEM")
                except discord.Forbidden as error:
                    group_fight_running = False
                    log(f"/group_fight : Fehlende Berechtigung beim Senden/Bearbeiten von Nachrichten! {error}", "ERROR")
                except Exception as error:
                    group_fight_running = False
                    log(f"/group_fight : Unerwarteter Fehler in on_timeout: {error}", "CRITICAL")


            @discord.ui.button(label="Beitreten", style=discord.ButtonStyle.green)
            async def join(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user.id in self.value:
                    return await interaction.response.send_message("Du bist bereits beigetreten!", ephemeral=True)
                if (await system.Get.user(interaction.user.id)).chocolate_eggs < bet:
                    return await interaction.response.send_message("Du hast nicht genug <:Schoko_Ei:1221556659030196284>!", ephemeral=True)
                if await system.Get.egg_check(interaction.user.id, "cooked") == False:
                    return await interaction.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
                self.value.append(interaction.user.id)
                await interaction.response.send_message("Du bist dem Gruppenkampf beigetreten!", ephemeral=True)
                await system.Update.last_fight(interaction.user.id)
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
        check = await system.Get.bake_check(ctx.author.id)
        if check == False:
            amount_uncooked = len(await system.Get.type_eggs_not_rotten(ctx.author.id, "uncooked"))
            amount_chocolate = (await system.Get.user(ctx.author.id)).chocolate_eggs
            embed = discord.Embed(title="Kuchen backen", description="Du hast nicht alle Zutaten, daher kann dir deine Oma nicht helfen!", color=discord.Color.red())
            embed.add_field(name="Zutaten", value=f"3x :egg: (Du besitzt: {amount_uncooked})\n10x <:Schoko_Ei:1221556659030196284> (Du besitzt: {amount_chocolate})", inline=False)
            embed.set_footer(text=f"Made by ItsKoga ❤")
            return await ctx.response.send_message(embed=embed, ephemeral=True)
        log(f"{ctx.author.name} hat ein kuchen gebacken!", "USER_ACTION")
        await system.Add.cake(ctx.author.id)
        embed = discord.Embed(title="Kuchen backen", description="Deine Oma hat dir geholfen einen :cake: zu backen! Da niemand von einer Oma klaut sind deine Punkte sicher!", color=discord.Color.green())
        await ctx.response.send_message(embed=embed, ephemeral=True)
        await system.Get.points(ctx.author.id)
        

    @slash_command(name="talisman", description="Zeigt dir deinen Eier Talisman", guild_only=True)
    @is_day()
    async def talisman(self, ctx, richtung: Option(str, "Wähle welche Chance dein Talisman erhöhen soll", choices=["Rohe Eier", "Ostereier"])): # type: ignore
        profile = await system.Get.user(ctx.author.id)
        if profile.egg_talisman == 0:
            return await ctx.response.send_message("Du hast noch keinen Eier Talisman!", ephemeral=True)
        if richtung == "Rohe Eier":
            await system.Update.user_egg_talisman(ctx.author.id, 2)
            await ctx.response.send_message("Dein Eier Talisman erhöht jetzt die Chance auf :egg:!", ephemeral=True)
        else:
            await system.Update.user_egg_talisman(ctx.author.id, 1)
            await ctx.response.send_message("Dein Eier Talisman erhöht jetzt die Chance auf <:osterei:962802014226640996>!", ephemeral=True)
        log(f"{ctx.author.name} hat seinen Talisman geändert!", "USER_ACTION")


    @slash_command(name="lose", description="Tausche ein Gekochtes Ei gegen ein Los", guild_only=True)
    @is_day()
    async def lose(self, ctx, amount: int):
        if amount < 1:
            return await ctx.response.send_message("Du musst mindestens 1 <:osterei:962802014226640996> eintauschen!", ephemeral=True)
        if amount > 25:
            return await ctx.response.send_message("Du kannst maximal 25 <:osterei:962802014226640996> auf einmal eintauschen!", ephemeral=True)
        if await system.Get.egg_check(ctx.author.id, "cooked") == False:
            return await ctx.response.send_message("Du hast kein <:osterei:962802014226640996>!", ephemeral=True)
        if len(await system.Get.type_eggs_not_rotten(ctx.author.id, "cooked")) < amount:
            return await ctx.response.send_message("Du hast nicht genug <:osterei:962802014226640996>!", ephemeral=True)
        log(f"{ctx.author.name} hat /lose ausgeführt!", "USER_ACTION")
        await system.Add.lose(ctx.author.id, amount)
        embed = discord.Embed(title="Verloren", description=f"Du hast {amount}x <:osterei:962802014226640996> eingetauscht!", color=0xec6726)
        embed.set_footer(text=f"Made by ItsKoga ❤")
        await ctx.response.send_message(embed=embed, ephemeral=True)
            

        
def setup(bot):
    bot.add_cog(Game(bot))
