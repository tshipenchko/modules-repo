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

from telethon.tl.functions.users import GetFullUserRequest

logger = logging.getLogger(__name__)


def register(cb):
    cb(UserInfoMod())


@loader.tds
class UserInfoMod(loader.Module):
    """Tells you about people"""
    strings = {"name": "User Info",
               "first_name": "First name: <code>{}</code>",
               "last_name": "\nLast name: <code>{}</code>",
               "id": "\nID: <code>{}</code>",
               "bio": "\nBio: <code>{}</code>",
               "restricted": "\nRestricted: <code>{}</code>",
               "deleted": "\nDeleted: <code>{}</code>",
               "bot": "\nBot: <code>{}</code>",
               "verified": "\nVerified: <code>{}</code>",
               "dc_id": "\nDC ID: <code>{}</code>",
               "find_error": "<b>Couldn't find that user.</b>",
               "no_args_or_reply": "<b>No args or reply was provided.</b>",
               "provide_user": "Provide a user to locate",
               "searching_user": "Searching for user...",
               "cannot_find": "Can't find user.",
               "permalink_txt": "<a href='tg://user?id={uid}'>{txt}</a>",
               "permalink_uid": "<a href='tg://user?id={uid}'>Permalink to {uid}</a>",
               "encode_cfg_doc": "Encode unicode characters"}

    def __init__(self):
        self.config = loader.ModuleConfig("ENCODE", False, lambda: self.strings["encode_cfg_doc"])

    def config_complete(self):
        self.name = self.strings["name"]

    def _handle_string(self, string):
        if self.config["ENCODE"]:
            return utils.escape_html(ascii(string))
        return utils.escape_html(string)

    async def userinfocmd(self, message):
        """Use in reply to get user info"""
        if message.is_reply:
            full = await self.client(GetFullUserRequest((await message.get_reply_message()).from_id))
        else:
            args = utils.get_args(message)
            if not args:
                return await utils.answer(message, self.strings["no_args_or_reply"])
            try:
                full = await self.client(GetFullUserRequest(args[0]))
            except ValueError:
                return await utils.answer(message, self.strings["find_error"])
        logger.debug(full)
        reply = self.strings["first_name"].format(self._handle_string(full.user.first_name))
        if full.user.last_name is not None:
            reply += self.strings["last_name"].format(self._handle_string(full.user.last_name))
        reply += self.strings["id"].format(utils.escape_html(full.user.id))
        reply += self.strings["bio"].format(self._handle_string(full.about))
        reply += self.strings["restricted"].format(utils.escape_html(str(full.user.restricted)))
        reply += self.strings["deleted"].format(utils.escape_html(str(full.user.deleted)))
        reply += self.strings["bot"].format(utils.escape_html(str(full.user.bot)))
        reply += self.strings["verified"].format(utils.escape_html(str(full.user.verified)))
        if full.user.photo:
            reply += self.strings["dc_id"].format(utils.escape_html(str(full.user.photo.dc_id)))
        await message.edit(reply)

    async def permalinkcmd(self, message):
        """Get permalink to user based on ID or username"""
        args = utils.get_args(message)
        if len(args) < 1:
            await message.edit(self.strings["provide_user"])
            return
        try:
            user = int(args[0])
        except ValueError:
            user = args[0]
        try:
            user = await self.client.get_entity(user)
        except ValueError as e:
            logger.debug(e)
            # look for the user
            await message.edit(self.strings["searching_user"])
            await self.client.get_dialogs()
            try:
                user = await self.client.get_entity(user)
            except ValueError:
                await message.edit(self.strings["cannot_find"])
                return
        if len(args) > 1:
            await utils.answer(message, self.strings["permalink_txt"].format(uid=user.id, txt=args[1]))
        else:
            await message.edit(self.strings["permalink_uid"].format(uid=user.id))

    async def client_ready(self, client, db):
        self.client = client
