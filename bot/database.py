# -*- coding: utf-8 -*-
import logging
import logging.config
import random
import sqlite3
from enum import Enum

import phrases

logging.config.fileConfig("logging.ini")
logger = logging.getLogger("database")

## === Classes === ##
class Category(Enum):
    """Categories in the database"""
    GREET = "3"
    LEFT_SERVER = "5"
    MENTION = "6,7"
    ONLINE = "8"
    SHUTDOWN = "9"


class Database(object):
    """ For reading and parsing lines in a SQLite database.

    Args:
        dbFile(unicode): The filepath of the database.
    """
    
    def __init__(self, db_file):
        self.db = db_file

    def get_column(self, header, table, maximum=None):
        """ Gets fields under a column header.

        Args:
            header(unicode): Name of column's header.
            table(unicode): Name of table.
            maximum(int, optional): Maximum amount of fields to fetch.

        Returns:
            fields(list): List of fields under header.
        """
        fields = []
        table = phrases.clean(table)
        connection = sqlite3.connect(self.db)
        connection.row_factory = lambda cursor, row: row[0]
        c = connection.cursor()
        if maximum:
            c.execute(f"SELECT {header} FROM {table} LIMIT ?", [maximum])
        else:
            c.execute(f"SELECT {header} FROM {table}")
        fields = c.fetchall()
        c.close()
        
        return fields

    def get_field(self, field_id, header, table):
        """ Gets the field under the specified header by its primary key value.

        Args:
            field_id(int, str): Unique ID of line the field is in.
            header(unicode): Header of the field to fetch.
            table(unicode): Name of table to look into.

        Returns:
            The desired field, or None if the lookup failed.

        Raises:
            TypeError: If field_id doesn't exist in the table.
        
        Examples:
            >>> get_field(123, "firstname", "kings")
            Adgar
        """
        header = phrases.clean(header)
        table = phrases.clean(table)
        field = None
        
        connection = sqlite3.connect(self.db)
        c = connection.cursor()

        statement = f"SELECT {header} FROM {table} WHERE id=?"
        logger.debug(statement)
        c.execute(statement, [field_id])

        try:
            field = c.fetchone()[0]
        except TypeError:
            logger.exception(f"ID '{field_id}' was not in table '{table}'")
        
        c.close()
        
        return field

    def get_ids(self, table, conditions=None, splitter=","):
        """ Gets the IDs that fit within the specified conditions.

        Gets all IDs if conditions is None.

        Args:
            table(unicode): Name of table to look into.
            conditions(list, optional): Categories you want to filter the line by:
                {"header of categories 1": "category1,category2",
                 "header of category 2": "category3"}
                Multiple categories under a single header are separated with a comma.

        Returns:
            ids(list): List of IDs that match the categories.

        Raises:
            OperationalError: If table or header doesn't exist.
            TypeError: If category is neither None nor a dictionary.

        Examples:
            >>> get_ids({"type": "greeting"})
            [1, 2, 3, 5, 9, 15]  # Any row that has the type "greeting".

            >>> get_ids({"type": "nickname,quip", "by": "Varric"})
            # Any row by "Varric" that has the type "nickname" or "quip".
            [23, 24, 25, 34, 37, 41, 42, 43]
        """
        ids = []
        table = phrases.clean(table)
        clause = ""
        
        connection = sqlite3.connect(self.db)
        connection.row_factory = lambda cursor, row: row[0]  # Gets first element for fetchall()

        c = connection.cursor()

        if conditions:
            clause = "WHERE ("
            clause_list = [clause,]
            substitutes = []
            cat_count = 1
            header_count = 1

            ## TODO: Add ability to specify comparison operator (e.g. =, <, LIKE, etc.)
            for con in conditions:
                if 1 < header_count:
                    clause_list.append(" AND (")

                sub_count = 1
                subconditions = conditions[con].split(splitter)
                for sub in subconditions:
                    if 1 < sub_count:
                        clause_list.append(" OR ")
                    
                    clause_list.append(f"{phrases.clean(con)}=?")
                    substitutes.append(sub)
                    sub_count += 2
                    
                clause_list.append(")")
                header_count += 2
                cat_count = 1

            clause = "".join(clause_list)

            statement = f"SELECT id FROM {table} {clause}"
            logger.debug(f"(get_ids) Substitutes: {substitutes}")
            logger.debug(f"(get_ids) SQLite statement: {statement}")

            c.execute(statement, substitutes)
        else:
            c.execute(f"SELECT id FROM {table}")

        ids = c.fetchall()

        return ids

    def random_line(self, header, table, conditions=None, splitter=","):
        """ Chooses a random line from the table under the header.

        Args:
            header(unicode): The header of the random line's column.
            table(unicode): Name of the table to look into.
            conditions(dict, optional): Categories to filter the line by:
                {"header of categories 1": "category1,category2",
                 "header of category 2": "category3"}
                Multiple categories under a single header are separated with a comma.
            splitter(unicode, optional): What separates multiple categories
                (default is a comma).

        Returns:
            line(unicode): A random line from the database.

        Raises:
            OperationalError: If header or table doesn't exist.
            TypeError: If category is neither None nor a dictionary.

        Examples:
            >>> random_line("line", {"type": "greeting"})
            Hello.
        """
        header = phrases.clean(header)
        table = phrases.clean(table)
        line = ""
        
        connection = sqlite3.connect(self.db)
        c = connection.cursor()

        if conditions:
            ids = self.get_ids(table, conditions, splitter)
            if ids:
                line = random.choice(ids)
                line = self.get_field(line, header, table)
        else:
            c.execute(f"SELECT {header} FROM {table} ORDER BY Random() LIMIT 1")  # TODO: Take categories into account.
            line = c.fetchone()[0]

        return line


class DiscordDatabase(Database):
    """ An extension of Database for Discord. """

    def add_server(self, server):
        """ Adds a server record to the database.

        Args:
            server(discord.Server): Server to add.

        """
        pass

    def remove_server(self, server):
        """ Removes a server from the database.

        Args:
            server(discord.Server): Server to remove.

        """
        pass


class BotDatabase(DiscordDatabase):
    """ An extension of DiscordDatabase for functions specific to the bot. """

    def add_song(self, url):
        """ Adds a song to the database.

        Args:
            url(str): URL of the song.
        """
        pass

    def add_playlist(self, name, user):
        """ Adds a playlist to the database.

        Playlists are bound to one user across all servers.

        Args:
            name(str): Name of the playlist.
            user(discord.Member/User): User who made the playlist.

        """
        pass

    def add_playlist_song(self, song, playlist):
        """ Adds a song to a playlist.

        Args:
            song(): Song to add.
            playlist(): The target playlist.

        """
        pass
    
