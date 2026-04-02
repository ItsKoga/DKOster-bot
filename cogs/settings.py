import discord
from discord.ext import commands
from discord.commands import slash_command

import log_helper
import system

log = log_helper.create("Settings")


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(
        name="notify",
        description="Schaltet die Benachrichtigungen an oder aus",
        guild_only=False,
    )
    async def notify(self, ctx):

        log(f"{ctx.author.name} hat die Benachrichtigungen umgestellt!", "USER_ACTION")

        # aktuellen Einstellung holen
        current = await system.Get.notifications(ctx.author.id)

        # Einstellung ändern    
        new_value = not current

        # 3) Cache updaten
        await system.Update.user_notifications(ctx.author.id, new_value)

        # 4) User Feedback
        await ctx.response.send_message(
            f"Benachrichtigungen wurden {'aktiviert' if new_value else 'deaktiviert'}!",
            ephemeral=True,
        )


def setup(bot: commands.Bot):
    bot.add_cog(Settings(bot))