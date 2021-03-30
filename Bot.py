import os
import logging
import threading

from telegram.ext import Updater, MessageQueue
from telegram.error import (TelegramError, ChatMigrated)
from telegram.utils.request import Request

from CommandHandlers.AliasCommandHandler import AliasCommandHandler
from CommandHandlers.ListCommandHandler import ListCommandHandler
from CommandHandlers.HelpCommandHandler import HelpCommandHandler
from CommandHandlers.RemoveCommandHandler import RemoveCommandHandler
from CommandHandlers.ClearCommandHandler import ClearCommandHandler
from CommandHandlers.OnCommandHandler import OnCommandHandler
from CommandHandlers.OffCommandHandler import OffCommandHandler
from CommandHandlers.LangCommandHandler import LangCommandHandler

from MessageHandlers.AliasMessageHandler import AliasMessageHandler

from CallbackQueryHandlers.LanguageCallbackQueryHandler import LanguageCallbackQueryHandler

from DbManager import DbManager
from HealthChecker import HealthChecker
from Localization.Localizer import Localizer

from MessageQueueBot import MessageQueueBot


class Bot(object):
    """description of class"""

    def __init__(self):
        token = 1796486170:AAGd11DiLzD5cdIs63cYiGHqCHIleBvvBSo
        message_queue = MessageQueue(all_burst_limit=29, all_time_limit_ms=1017)
        request = Request(con_pool_size=8)
        bot = MessageQueueBot(token, request=request, message_queue=message_queue)

        self._updater = Updater(bot=bot)
        self._dispatcher = self._updater.dispatcher

        self._db_manager = DbManager()
        self._localizer = Localizer(self._db_manager)

        self._health_checker = HealthChecker(self._updater.bot, self._db_manager)
        self._health_check_interval = int(os.environ.get('HEALTH_CHECK_INTERVAL'))

        self.__setup_command_handlers()
        self.__setup_callback_query_handlers()
        self.__setup_message_handlers()
        self.__setup_error_handler()

    def start(self):
        logging.info('Starting the bot...')
        self._updater.start_polling()
        self.__perform_health_check()
        logging.info('Bot is started')
        self._updater.idle()

    def stop(self):
        logging.info('Stopping the bot...')
        self._updater.stop()
        logging.info('Bot is stopped')

    def error_callback(self, bot, update, error):
        try:
            logging.error('Error occurred: %s' % error.message)
            raise error
        except ChatMigrated as e:
            self._db_manager.update_chat_id(update.message.chat_id, e.new_chat_id)
        except TelegramError as e:
            logging.error('Unknown error: %s' % e.message)

    def __perform_health_check(self):
        self._health_checker.perform_health_check()
        timer = threading.Timer(self._health_check_interval, self.__perform_health_check)
        timer.start()

    def __setup_error_handler(self):
        self._dispatcher.add_error_handler(self.error_callback)

    def __setup_command_handlers(self):
        handlers = [
            AliasCommandHandler(self._db_manager, self._localizer),
            ListCommandHandler(self._db_manager, self._localizer),
            HelpCommandHandler(self._localizer),
            RemoveCommandHandler(self._db_manager, self._localizer),
            ClearCommandHandler(self._db_manager, self._localizer),
            OnCommandHandler(self._db_manager, self._localizer),
            OffCommandHandler(self._db_manager, self._localizer),
            LangCommandHandler(self._db_manager, self._localizer)
        ]

        for handler in handlers:
            self._dispatcher.add_handler(handler)

    def __setup_message_handlers(self):
        handlers = [
            AliasMessageHandler(self._db_manager)
        ]

        for handler in handlers:
            self._dispatcher.add_handler(handler)

    def __setup_callback_query_handlers(self):
        handlers = [
            LanguageCallbackQueryHandler(self._db_manager, self._localizer)
        ]

        for handler in handlers:
            self._dispatcher.add_handler(handler)
