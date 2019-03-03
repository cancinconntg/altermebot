import logging

from telegram.ext import CommandHandler
from telegram import ParseMode


class OnCommandHandler(CommandHandler):
    """description of class"""

    def __init__(self, aliases_storage):
        super().__init__('on', self.__handle)
        self._aliases_storage = aliases_storage

    def __handle(self, bot, update):
        logging.info('/on: entered')

        message = update.message
        chat_id = message.chat_id
        user_id = message.from_user.id

        user = message.from_user
        mention = user.username
        parse_mode = None
        if not mention:
            mention = '[%s](tg://user?id=%d)' % (user.full_name, user_id)
            parse_mode = ParseMode.MARKDOWN
        else:
            mention = "@%s" % mention

        self._aliases_storage.enable_aliasing(user_id, chat_id)

        bot.send_message(chat_id=chat_id,
                         text="%s, you will be mentioned by your aliases in this chat from now" % mention,
                         parse_mode=parse_mode)

        logging.info('/on: exited')