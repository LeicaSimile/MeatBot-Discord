# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import logging
import logging.config

import chatbot
import settings

logging.config.fileConfig("logging.ini")
logger = logging.getLogger("main")

def main():
    description = ":D"
    bot = commands.Bot(settings.BOT_PREFIX, description=description, pm_help=True)
    meatbot = chatbot.Bot(bot, settings.FILE_DATABASE)
    meatbot.run(settings.TOKEN)


if "__main__" == __name__:
    main()
