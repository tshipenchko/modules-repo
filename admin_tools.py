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

from .. import loader, utils, security
import logging

from telethon.tl.types import ChatAdminRights, ChatBannedRights, PeerUser, PeerChannel
from telethon.errors import BadRequestError
from telethon.tl.functions.channels import EditAdminRequest, EditBannedRequest
from telethon.tl.functions.messages import EditChatAdminRequest

logger = logging.getLogger(__name__)


@loader.tds
class BanMod(loader.Module):
    """Задачи группового администрирования"""
    strings = {"name": "Administration",
               "ban_not_supergroup": "<b>Я не могу забанить кого-то, если он не в супергруппе!</b>",
               "unban_not_supergroup": "<b>Я не могу снять бан с кого-либо, если он не забанен в супергруппе!</b>",
               "kick_not_group": "<b>Я не могу исключить кого-то, если он не в группе!</b>",
               "mute_not_supergroup": "<b>Я не могу заглушить кого-то, если он не в супергруппе!</b>",
               "unmute_not_supergroup": "<b>Я не могу вернуть голос кому-то, если он не в супергруппе!</b>",
               "ban_none": "<b>Я не могу никого забанить, не так ли?</b>",
               "unban_none": "<b>Мне нужен кто-то, чтобы разбанить его.</b>",
               "kick_none": "<b>Мне нужен кто-то, чтобы исключить его из чата.</b>",
               "promote_none": "<b>Я не могу никому повышать права, не так ли?</b>",
               "demote_none": "<b>Я не могу никому понизить права, не так ли?</b>",
               "mute_none": "<b>Я не могу никого заглушить, не так ли?</b>",
               "unmute_none": "<b>Я не могу никому вернуть голос, не так ли?</b>",
               "who": "<b>Кто это, черт возьми?</b>",
               "not_admin": "<b>Разве я админ здесь?</b>",
               "banned": "<code>{}</code> <b>забанен в чате!</b>",
               "unbanned": "<code>{}</code> <b>разбанен в чате!</b>",
               "kicked": "<code>{}</code> <b>исключён с чата!</b>",
               "promoted": "<code>{}</code> <b>теперь с правами администратора!</b>",
               "demoted": "<code>{}</code> <b>теперь без прав администратора!</b>",
               "muted": "<code>{}</code> <b>заглушён!</b>",
               "unmuted": "<code>{}</code> <b>вернул себе возможность писать!</b>"}

    @loader.group_admin_ban_users
    @loader.ratelimit
    async def bancmd(self, message):
        """Забанить пользователя в группе."""
        if not isinstance(message.to_id, PeerChannel):
            return await utils.answer(message, self.strings("ban_not_supergroup", message))
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings("ban_none", message))
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings("who", message))
        logger.debug(user)
        try:
            await self.client(EditBannedRequest(message.chat_id, user.id,
                                                ChatBannedRights(until_date=None, view_messages=True)))
        except BadRequestError:
            await utils.answer(message, self.strings("not_admin", message))
        else:
            await self.allmodules.log("ban", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message,
                               self.strings("banned", message).format(utils.escape_html(ascii(user.first_name))))

    @loader.group_admin_ban_users
    @loader.ratelimit
    async def unbancmd(self, message):
        """Снять бан с пользователя."""
        if not isinstance(message.to_id, PeerChannel):
            return await utils.answer(message, self.strings("not_supergroup", message))
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings("unban_none", message))
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings("who", message))
        logger.debug(user)
        try:
            await self.client(EditBannedRequest(message.chat_id, user.id,
                              ChatBannedRights(until_date=None, view_messages=False)))
        except BadRequestError:
            await utils.answer(message, self.strings("not_admin", message))
        else:
            await self.allmodules.log("unban", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message,
                               self.strings("unbanned", message).format(utils.escape_html(ascii(user.first_name))))

    @loader.group_admin_ban_users
    @loader.ratelimit
    async def kickcmd(self, message):
        """Исключить пользователя из группы."""
        if isinstance(message.to_id, PeerUser):
            return await utils.answer(message, self.strings("not_group", message))
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings("kick_none", message))
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings("who", message))
        logger.debug(user)
        if user.is_self:
            if not (await message.client.is_bot()
                    or await self.allmodules.check_security(message, security.OWNER | security.SUDO)):
                return
        try:
            await self.client.kick_participant(message.chat_id, user.id)
        except BadRequestError:
            await utils.answer(message, self.strings("not_admin", message))
        else:
            await self.allmodules.log("kick", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message,
                               self.strings("kicked", message).format(utils.escape_html(ascii(user.first_name))))

    @loader.group_admin_add_admins
    @loader.ratelimit
    async def promotecmd(self, message):
        """Предоставляет права администратора указанному пользователю."""
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if not args:
                return await utils.answer(message, self.strings("promote_none", message))
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings("who", message))
        rank = ""
        if len(args) >= 1:
            rank = args[1]
        logger.debug(user)
        try:
            if message.is_channel:
                await self.client(EditAdminRequest(message.chat_id, user.id,
                                                   ChatAdminRights(post_messages=None,
                                                                   add_admins=None,
                                                                   invite_users=None,
                                                                   change_info=None,
                                                                   ban_users=None,
                                                                   delete_messages=True,
                                                                   pin_messages=True,
                                                                   edit_messages=None), rank))
        except BadRequestError:
            await utils.answer(message, self.strings("not_admin", message))
        else:
            await self.allmodules.log("promote", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message,
                               self.strings("promoted", message).format(utils.escape_html(ascii(user.first_name))))

    @loader.group_admin_add_admins
    async def demotecmd(self, message):
        """Лишает прав администратора указанной группы администраторов."""
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings("demote_none", message))
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings("who", message))
        logger.debug(user)
        try:
            if message.is_channel:
                await self.client(EditAdminRequest(message.chat_id, user.id,
                                                   ChatAdminRights(post_messages=None,
                                                                   add_admins=None,
                                                                   invite_users=None,
                                                                   change_info=None,
                                                                   ban_users=None,
                                                                   delete_messages=None,
                                                                   pin_messages=None,
                                                                   edit_messages=None), ""))
            else:
                await self.client(EditChatAdminRequest(message.chat_id, user.id, False))
        except BadRequestError:
            await utils.answer(message, self.strings("not_admin", message))
        else:
            await self.allmodules.log("demote", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message,
                               self.strings("demoted", message).format(utils.escape_html(ascii(user.first_name))))

    async def mutecmd(self, message):
        """Заглушает пользователя в группе."""
        if not isinstance(message.to_id, PeerChannel):
            return await utils.answer(message, self.strings("mute_not_supergroup", message))
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings("mute_none", message))
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings("who", message))
        logger.debug(user)
        try:
            await self.client(EditBannedRequest(message.chat_id, user.id,
                                                ChatBannedRights(until_date=None, send_messages=True)))
        except BadRequestError:
            await utils.answer(message, self.strings("not_admin", message))
        else:
            await self.allmodules.log("mute", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message, self.strings("muted",
                                                     message).format(utils.escape_html(ascii(user.first_name))))

    async def unmutecmd(self, message):
        """Вернуть голос пользователю в группе."""
        if not isinstance(message.to_id, PeerChannel):
            return await utils.answer(message, self.strings("unmute_not_supergroup", message))
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings("unmute_none", message))
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings("who", message))
        logger.debug(user)
        try:
            await self.client(EditBannedRequest(message.chat_id, user.id, ChatBannedRights(until_date=None,
                                                view_messages=None, send_messages=False, send_media=False,
                                                send_stickers=False, send_gifs=False, send_games=False,
                                                send_inline=False, embed_links=False)))
        except BadRequestError:
            await utils.answer(message, self.strings("not_admin", message))
        else:
            await self.allmodules.log("unmute", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message, self.strings("unmuted",
                                                     message).format(utils.escape_html(ascii(user.first_name))))

    async def client_ready(self, client, db):
        self.client = client
