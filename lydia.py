# Some parts are Copyright (C) Diederik Noordhuis (@AntiEngineer) 2019
# All licensed under project license

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

# requires: coffeehouse>=2.2.0

from .. import loader, utils
import logging
import asyncio
import time
import random
import coffeehouse
from telethon import functions, types

logger = logging.getLogger(__name__)


@loader.tds
class LydiaMod(loader.Module):
    """Беседа с роботом вместо человека."""
    strings = {"name": "Лидия",
               "enable_disable_error_group": "<b>Служба ИИ не может быть"
               " включена или отключена в этом чате. Может быть это не групповой чат?</b>",
               "enable_error_user": "<b>Служба ИИ не может быть"
               " включена для этого пользователя. Возможно она ещё не была для него отключена?</b>",
               "successfully_enabled": "<b>ИИ включен для этого пользователя. </b>",
               "successfully_enabled_for_chat": "<b>ИИ включен для этого пользователя в этом чате.</b>",
               "cannot_find": "<b>Не могу найти этого пользователя.</b>",
               "successfully_disabled": "<b>ИИ отключен для этого пользователя.</b>",
               "cleanup_ids": "<b>Успешно убраны идентификаторы с отключенной Лидией</b>",
               "cleanup_sessions": "<b>Успешно очищены сессии Лидии.</b>",
               "doc_client_key": "Ключ API для Лидии нужно получить на сайте"
               " https://coffeehouse.intellivoid.net",
               "doc_ignore_no_common": "Игнорирование пользователей, не имеющих общих чатов с вами.",
               "doc_disabled": "По умолчанию Лидия включена"
                               " в приватных чатах (если True, вам придется использовать .forcelydia"}

    def __init__(self):
        self.config = loader.ModuleConfig("CLIENT_KEY", None, lambda m: self.strings("doc_client_key", m),
                                          "IGNORE_NO_COMMON", False, lambda m: self.strings("doc_ignore_no_common", m),
                                          "DISABLED", False, lambda m: self.strings("doc_disabled", m))
        self._ratelimit = []
        self._cleanup = None
        self._lydia = None

    async def client_ready(self, client, db):
        self._db = db
        self._lydia = coffeehouse.LydiaAI(self.config["CLIENT_KEY"]) if self.config["CLIENT_KEY"] else None
        # Schedule cleanups
        self._cleanup = asyncio.ensure_future(self.schedule_cleanups())

    async def schedule_cleanups(self):
        """Удаляет мертвые сессии и перепланирует себя для запуска после истечения следующего сеанса."""
        sessions = self._db.get(__name__, "sessions", {})
        if len(sessions) == 0:
            return
        nsessions = {}
        t = time.time()
        for ident, session in sessions.items():
            if not session["expires"] < t:
                nsessions.update({ident: session})
            else:
                break  # workaround server bug
                session = await utils.run_sync(self._lydia.get_session, session["session_id"])
                if session.available:
                    nsessions.update({ident: session})
        if len(nsessions) > 1:
            next = min(*[v["expires"] for k, v in nsessions.items()])
        elif len(nsessions) == 1:
            [next] = [v["expires"] for k, v in nsessions.items()]
        else:
            next = t + 86399
        if nsessions != sessions:
            self._db.set(__name__, "sessions", nsessions)
        # Don't worry about the 1 day limit below 3.7.1, if it isn't expired we will just reschedule,
        # as nothing will be matched for deletion.
        await asyncio.sleep(min(next - t, 86399))

        await self.schedule_cleanups()

    async def enlydiacmd(self, message):
        """Включает Лидию для конкретного пользователя."""
        old = self._db.get(__name__, "allow", [])
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await utils.answer(message, self.strings("enable_disable_error_group", message))
            return
        try:
            old.remove(user)
            self._db.set(__name__, "allow", old)
        except ValueError:
            await utils.answer(message, self.strings("enable_error_user", message))
            return
        await utils.answer(message, self.strings("successfully_enabled", message))

    async def forcelydiacmd(self, message):
        """Включает Лидию для пользователя в конкретном чате."""
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await utils.answer(message, self.strings("cannot_find", message))
            return
        self._db.set(__name__, "force", self._db.get(__name__, "force", []) + [[utils.get_chat_id(message), user]])
        await utils.answer(message, self.strings("successfully_enabled_for_chat", message))

    async def dislydiacmd(self, message):
        """Отключает Лидию для конкретного пользователя."""
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await utils.answer(message, self.strings("enable_disable_error_group", message))
            return

        old = self._db.get(__name__, "force")
        try:
            old.remove([utils.get_chat_id(message), user])
            self._db.set(__name__, "force", old)
        except (ValueError, TypeError, AttributeError):
            pass
        self._db.set(__name__, "allow", self._db.get(__name__, "allow", []) + [user])
        await utils.answer(message, self.strings("successfully_disabled", message))

    async def cleanlydiadisabledcmd(self, message):
        """ Удаление всех пользователей с ограниченными возможностями из базы данных. """
        self._db.set(__name__, "allow", [])
        return await utils.answer(message, self.strings("cleanup_ids", message))

    async def cleanlydiasessionscmd(self, message):
        """Удаление всех активных и не активных сеансов Лидии из базы данных."""
        self._db.set(__name__, "sessions", {})
        return await utils.answer(message, self.strings("cleanup_sessions", message))

    async def watcher(self, message):
        if not self.config["CLIENT_KEY"]:
            logger.debug("no key set for lydia, returning")
            return
        if not isinstance(message, types.Message):
            return
        if self._lydia is None:
            self._lydia = coffeehouse.LydiaAI(self.config["CLIENT_KEY"])
        if (isinstance(message.to_id, types.PeerUser) and not self.get_allowed(message.from_id)) or \
                self.is_forced(utils.get_chat_id(message), message.from_id):
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            else:
                if not isinstance(message.message, str):
                    return
                if len(message.message) == 0:
                    return
                if self.config["IGNORE_NO_COMMON"] and not self.is_forced(utils.get_chat_id(message), message.from_id):
                    fulluser = await message.client(functions.users.GetFullUserRequest(await utils.get_user(message)))
                    if fulluser.common_chats_count == 0:
                        return
                await message.client(functions.messages.SetTypingRequest(
                    peer=await utils.get_user(message),
                    action=types.SendMessageTypingAction()
                ))
                try:
                    # Get a session
                    sessions = self._db.get(__name__, "sessions", {})
                    session = sessions.get(utils.get_chat_id(message), None)
                    if session is None or session["expires"] < time.time():
                        session = await utils.run_sync(self._lydia.create_session)
                        session = {"session_id": session.id, "expires": session.expires}
                        logger.debug(session)
                        sessions[utils.get_chat_id(message)] = session
                        logger.debug(sessions)
                        self._db.set(__name__, "sessions", sessions)
                        if self._cleanup is not None:
                            self._cleanup.cancel()
                        self._cleanup = asyncio.ensure_future(self.schedule_cleanups())
                    logger.debug(session)
                    # AI Response method
                    msg = message.message
                    airesp = await utils.run_sync(self._lydia.think_thought, session["session_id"], str(msg))
                    logger.debug("AI says %s", airesp)
                    if random.randint(0, 1) and isinstance(message.to_id, types.PeerUser):
                        await message.respond(airesp)
                    else:
                        await message.reply(airesp)
                finally:
                    await message.client(functions.messages.SetTypingRequest(
                        peer=await utils.get_user(message),
                        action=types.SendMessageCancelAction()
                    ))

    def get_allowed(self, id):
        if self.config["DISABLED"]:
            return True
        return id in self._db.get(__name__, "allow", [])

    def is_forced(self, chat, user_id):
        forced = self._db.get(__name__, "force", [])
        if [chat, user_id] in forced:
            return True
        else:
            return False
