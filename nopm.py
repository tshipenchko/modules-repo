#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .. import loader, utils

import logging

from telethon import functions, types

logger = logging.getLogger(__name__)


@loader.tds
class AntiPMMod(loader.Module):
    """Запрещает людям отправлять вам нежелательные личные сообщения."""
    strings = {"name": "Anti-PM",
               "limit_cfg_doc": "Максимальное количество личных сообщений перед блокировкой пользователя, или же ни одного",
               "who_to_block": "<b>Укажите, кого заблокировать</b>",
               "blocked": ("<b>Я не хочу никаких личных сообщений от</b> <a href='tg://user?id={}'>тебя</a>, "
                           "<b>поэтому вы заблокированы!</b>"),
               "who_to_unblock": "<b>Укажите, кого разблокировать</b>",
               "unblocked": ("<b>Ну хорошо! Я прощу его на этот раз. Личные сообщения были разблокированы для </b> "
                             "<a href='tg://user?id={}'>этого пользователя</a>"),
               "who_to_allow": "<b>Кого мне разрешить в личную переписку?</b>",
               "allowed": "<b>Я позволил</b> <a href='tg://user?id={}'>тебе</a> <b>писать мне в личные сообщения сейчас.</b>",
               "who_to_report": "<b>На кого надо жаловаться?</b>",
               "reported": "<b>Вы только что пожаловались о спаме!</b>",
               "who_to_deny": "<b>Кому мне запретить в личные сообщения?</b>",
               "denied": ("<b>Я отказался от личных сообщений от</b> <a href='tg://user?id={}'>тебя</a> "
                          "<b>.</b>"),
               "notif_off": "<b>Уведомления от отклоненных личных сообщений заглушены.</b>",
               "notif_on": "<b>Уведомления от отклоненных личных сообщений активированы.</b>",
               "go_away": ("Приветствую! К сожалению, я не принимаю личные сообщения от "
                            "незнакомцев.\n\nПожалуйста, свяжитесь со мной в группе, или <b>подождите</b> "
                            ", пока я вас одобрю"),
               "triggered": ("Привет! Я не ценю то, что ты врываешься в личную переписку со мной как сейчас! "
                             "Вы просили меня одобрить вас в личные сообщения? Нет? Тогда пока."
                             "\n\nPS: Жалоба на спам уже отправлена.")}

    def __init__(self):
        self.config = loader.ModuleConfig("PM_BLOCK_LIMIT", None, lambda m: self.strings("limit_cfg_doc", m))
        self._me = None
        self._ratelimit = []

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me(True)

    async def blockcmd(self, message):
        """Заблокировать этого пользователя в личных сообщениях без предупреждения."""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings("who_to_block", message))
            return
        await message.client(functions.contacts.BlockRequest(user))
        await utils.answer(message, self.strings("blocked", message).format(user))

    async def unblockcmd(self, message):
        """Разблокировать этого пользователя в личных сообщениях."""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings("who_to_unblock", message))
            return
        await message.client(functions.contacts.UnblockRequest(user))
        await utils.answer(message, self.strings("unblocked", message).format(user))

    async def allowcmd(self, message):
        """Разрешить этому пользователю писать Вам в личные сообщения."""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings("who_to_allow", message))
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).union({user})))
        await utils.answer(message, self.strings("allowed", message).format(user))

    async def reportcmd(self, message):
        """Сообщить о спаме пользователя. Используйте только в личных сообщениях."""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings("who_to_report", message))
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).difference({user})))
        if message.is_reply and isinstance(message.to_id, types.PeerChannel):
            # Report the message
            await message.client(functions.messages.ReportRequest(peer=message.chat_id,
                                                                  id=[message.reply_to_msg_id],
                                                                  reason=types.InputReportReasonSpam()))
        else:
            await message.client(functions.messages.ReportSpamRequest(peer=message.to_id))
        await utils.answer(message, self.strings("reported", message))

    async def denycmd(self, message):
        """Запретить этого пользователя в личных сообщениях без предупреждения."""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings("who_to_deny", message))
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).difference({user})))
        await utils.answer(message, self.strings("denied", message).format(user))

    async def notifoffcmd(self, message):
        """Отключить уведомления от запрещенных личных сообщений."""
        self._db.set(__name__, "notif", True)
        await utils.answer(message, self.strings("notif_off", message))

    async def notifoncmd(self, message):
        """Включить уведомления от запрещенных личных сообщений."""
        self._db.set(__name__, "notif", False)
        await utils.answer(message, self.strings("notif_on", message))

    async def watcher(self, message):
        if not isinstance(message, types.Message):
            return
        if getattr(message.to_id, "user_id", None) == self._me.user_id:
            logger.debug("pm'd!")
            if message.from_id in self._ratelimit:
                self._ratelimit.remove(message.from_id)
                return
            else:
                self._ratelimit += [message.from_id]
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            if self.get_allowed(message.from_id):
                logger.debug("Authorised pm detected")
            else:
                await utils.answer(message, self.strings("go_away", message))
                if isinstance(self.config["PM_BLOCK_LIMIT"], int):
                    limit = self._db.get(__name__, "limit", {})
                    if limit.get(message.from_id, 0) >= self.config["PM_BLOCK_LIMIT"]:
                        await utils.answer(message, self.strings("triggered", message))
                        await message.client(functions.contacts.BlockRequest(message.from_id))
                        await message.client(functions.messages.ReportSpamRequest(peer=message.from_id))
                        del limit[message.from_id]
                        self._db.set(__name__, "limit", limit)
                    else:
                        self._db.set(__name__, "limit", {**limit, message.from_id: limit.get(message.from_id, 0) + 1})
                if self._db.get(__name__, "notif", False):
                    await message.client.send_read_acknowledge(message.chat_id)

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])
