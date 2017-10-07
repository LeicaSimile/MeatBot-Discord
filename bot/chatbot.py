# -*- coding: utf-8 -*-
import discord
import logging
import logging.config

from context import GeneralContext
import commands
import database
import phrases
import settings

logging.config.fileConfig("logging.ini")
logger = logging.getLogger("bot")


class Bot(object):
    """
    Attributes:
        bot(discord.Bot): The bot instance.
        db_file(str): File path of the bot's database. Used to create 'db',
            a Database instance.
    """
    
    def __init__(self, bot, db_file):
        self.client = bot
        self.db = database.Database(db_file)

    def run(self, token):
        self.set_events()
        self.set_commands()
        self.client.run(token)

    def event_member_join(self):
        async def on_member_join(member):
            server = member.server
            response = self.get_phrase(phrases.Category.GREET.value)
            ctx = GeneralContext(server=server, user=member)
            
            response = self.parse(response, context=ctx)
            await self.client.send_message(server, response)

        return on_member_join

    def event_ready(self):
        async def on_ready():
            logger.info(f"{self.client.user.name} is now online.")
            logger.info(f"ID: {self.client.user.id}")
            logger.info(f"Command prefix: {settings.BOT_PREFIX}")

            status = settings.BOT_STATUS
            await self.client.change_presence(game=discord.Game(name=status))

        return on_ready

    def get_phrase(self, category):
        """ Shortcut for getting a random phrase from the database.

        Args:
            category(unicode): The phrase category - see enum 'Category' in phrases.py.
        """
        return self.db.random_line("line", "phrases", {"category_id": category})

    def parse(self, text, context=None, substitutions=None):
        """ Interprets a string and formats accordingly, substitutes values, etc.

        Args:
            text(unicode): String to parse.
            context(GeneralContext, optional): Current context of the message.
            substitutions(dict, optional): Other substitutions to perform.
                Replaces key with corresponding value.

        Returns:
            text(unicode): Parsed string.
        """
        if not substitutions: substitutions = {}
        text = phrases.parse_all(text)

        ## Add context variables to substitutions.
        substitutions[settings.BOT_DISPLAY_NAME] = self.client.user.name
        substitutions[settings.BOT_NAME] = self.client.user.display_name
        substitutions[settings.EMOTE] = "/me"

        try:
            ## Channel variables
            substitutions[settings.CHANNEL_NAME] = context.channel.name
        except AttributeError:
            substitutions[settings.CHANNEL_NAME] = ""
            
        try:
            ## User (author) variables
            substitutions[settings.DISPLAY_NAME] = context.user.display_name
            substitutions[settings.MENTION] = context.user.mention
            substitutions[settings.USER_NAME] = context.user.name
        except AttributeError:
            substitutions[settings.DISPLAY_NAME] = ""
            substitutions[settings.MENTION] = ""
            substitutions[settings.USER_NAME] = ""
            
        try:
            ## Server variables
            substitutions[settings.SERVER_NAME] = context.server.name
        except AttributeError:
            substitutions[settings.SERVER_NAME] = ""

        for s in substitutions:
            if not substitutions[s]:
                substitutions[s] = ""
                
            text = text.replace(s, substitutions[s])
            logger.debug(f"parse(): {text} (replaced '{s}' with '{substitutions[s]}')")
        
        return text

    async def say(self, destination, message, context=None):
        message = self.parse(message, context)
        await self.client.send_message(destination, message)
    
    def set_commands(self):
        self.client.add_cog(commands.General(self))
        self.client.add_cog(commands.Debugging(self))
        
    def set_events(self):
        self.client.event(self.event_ready())
        self.client.event(self.event_member_join())
