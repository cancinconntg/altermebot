import sqlite3
import re
import logging

from BotUtils import ALIASING_ENABLED, ALIASING_DISABLED


class AliasesStorage(object):
    """description of class"""

    def __init__(self):
        self._connection = sqlite3.connect("alterme.db", check_same_thread=False)
        self._connection.create_function('regexp', 2, self.__regexp)
        self._connection.create_function('eqnocase', 2, self.__eqnocase)

        self._cursor = self._connection.cursor()

        self.__create_tables()

    def get_aliases_count(self, user_id, chat_id):
        logging.info('[AS] get aliases count for user %d in chat %d' % (user_id, chat_id))
        (count,) = self._cursor.execute('''SELECT COUNT(*)
                                           FROM aliases
                                           WHERE user_id = ? AND
                                                 chat_id = ?''', (user_id, chat_id)).fetchone()
        return count

    def check_alias_is_not_in_use(self, user_id, chat_id, alias):
        logging.info('[AS] check for user %d that alias "%s" is not in use in chat %d' % (user_id, alias, chat_id))
        user_id_row = self._cursor.execute('''SELECT user_id
                                              FROM aliases
                                              WHERE chat_id = ? AND
                                                    EQNOCASE(alias, ?)''', (chat_id, alias)).fetchone()
        if user_id_row is None:
            return True

        return user_id_row[0] == user_id

    def add_alias(self, user_id, chat_id, alias):
        logging.info('[AS] add alias "%s" for user %d in chat %d' % (alias, user_id, chat_id))
        self._cursor.execute('''INSERT OR IGNORE INTO aliases(user_id, chat_id, alias, date)
                                VALUES (?, ?, ?, datetime('now'))''', (user_id, chat_id, alias))
        self._connection.commit()

    def remove_alias(self, user_id, chat_id, alias):
        logging.info('[AS] remove alias "%s" for user %d in chat %d' % (alias, user_id, chat_id))
        self._cursor.execute('''DELETE
                                FROM aliases
                                WHERE user_id = ? AND
                                      EQNOCASE(alias, ?) AND
                                      chat_id = ?''', (user_id, alias, chat_id))
        self._connection.commit()

    def remove_all_aliases(self, user_id, chat_id):
        logging.info('[AS] remove all aliases for user %d in chat %d' % (user_id, chat_id))
        self._cursor.execute('''DELETE
                                FROM aliases
                                WHERE user_id = ? AND
                                      chat_id = ?''', (user_id, chat_id))
        self._connection.commit()

    def get_aliases(self, user_id, chat_id):
        logging.info('[AS] get all aliases for user %d in chat %d' % (user_id, chat_id))
        rows = self._cursor.execute('''SELECT alias
                                       FROM aliases
                                       WHERE user_id = ? AND
                                             chat_id = ?''', (user_id, chat_id)).fetchall()
        return list(map(lambda row: row[0], rows))

    def contains_alias(self, text, chat_id):
        logging.info('[AS] check string "%s" contains aliases for chat %d' % (text, chat_id))
        rows = self._cursor.execute('''SELECT user_id
                                       FROM aliases
                                       WHERE chat_id = ? AND
                                             alias REGEXP ? ''', (chat_id, text)).fetchall()
        return list(map(lambda row: row[0], rows))

    def enable_aliasing(self, user_id, chat_id):
        logging.info('[AS] enable aliasing for user %d in chat %d' % (user_id, chat_id))
        self._cursor.execute('''INSERT OR REPLACE INTO states(user_id, chat_id, state)
                                VALUES (?, ?, ?)''', (user_id, chat_id, ALIASING_ENABLED))
        self._connection.commit()

    def disable_aliasing(self, user_id, chat_id):
        logging.info('[AS] disable aliasing for user %d in chat %d' % (user_id, chat_id))
        self._cursor.execute('''INSERT OR REPLACE INTO states(user_id, chat_id, state)
                                VALUES (?, ?, ?)''', (user_id, chat_id, ALIASING_DISABLED))
        self._connection.commit()

    def is_aliasing_enabled(self, user_id, chat_id):
        logging.info('[AS] check if aliasing enabled for user %d in chat %d' % (user_id, chat_id))
        state_row = self._cursor.execute('''SELECT state
                                            FROM states
                                            WHERE chat_id = ? AND
                                                  user_id = ?''', (chat_id, user_id)).fetchone()
        if state_row is None:
            return True

        return state_row[0] == ALIASING_ENABLED
    
    def log_command(self, user_id, chat_id, command, args):
        self._cursor.execute('''INSERT OR IGNORE INTO commands(user_id, chat_id, command, args, date)
                                VALUES (?, ?, ?, ?, datetime('now'))''', (user_id, chat_id, command, args))
        self._connection.commit()

    @staticmethod
    def __regexp(text, alias):
        return 1 if alias and re.search(r'(?i)\b%s\b' % re.escape(alias), text) else 0

    @staticmethod
    def __eqnocase(x, y):
        return 1 if x.lower() == y.lower() else 0

    def __create_tables(self):
        self.__create_aliases_table()
        self.__create_states_table()
        self.__create_commands_table()

    def __create_aliases_table(self):
        self._cursor.execute('''CREATE TABLE IF NOT EXISTS aliases (
                                id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                user_id INTEGER NOT NULL,
                                chat_id INTEGER NOT NULL,
                                alias   TEXT NOT NULL,
                                date    TEXT NOT NULL,
                                UNIQUE (user_id, chat_id, alias))''')

    def __create_states_table(self):
        self._cursor.execute('''CREATE TABLE IF NOT EXISTS states (
                                id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                user_id INTEGER NOT NULL,
                                chat_id INTEGER NOT NULL,
                                state   INTEGER NOT NULL,
                                UNIQUE (user_id, chat_id))''')
        
    def __create_commands_table(self):
        self._cursor.execute('''CREATE TABLE IF NOT EXISTS commands (
                                id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                user_id INTEGER NOT NULL,
                                chat_id INTEGER NOT NULL,
                                command TEXT NOT NULL,
                                args    TEXT,
                                date    TEXT NOT NULL)''')
