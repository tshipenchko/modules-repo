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

# requires: https://github.com/LonamiWebs/Telethon/archive/master.zip

import asyncio
import logging

from telethon.tl.types import InputMediaDice

from .. import loader, utils, security

logger = logging.getLogger(__name__)


@loader.tds
class DiceMod(loader.Module):
    """Кубик"""
    strings = {"name": "Кубик"}

    def __init__(self):
        self.config = loader.ModuleConfig("POSSIBLE_VALUES", {"": [1, 2, 3, 4, 5, 6],
                                                              "🎲": [1, 2, 3, 4, 5, 6],
                                                              "🎯": [1, 2, 3, 4, 5, 6],
                                                              "🏀": [1, 2, 3, 4, 5]},
                                          "Возможные варианты эмодзи")

    @loader.unrestricted
    async def dicecmd(self, message):
        """Крутит кубик (возможно добавление необходимого значения)
           .dice <эмодзи> <результат> <кол-во>"""
        args = utils.get_args(message)
        if await self.allmodules.check_security(message, security.OWNER | security.SUDO):
            try:
                emoji = args[0]
            except IndexError:
                emoji = "🎲"
            possible = self.config["POSSIBLE_VALUES"].get(emoji, None)
            if possible is None:
                emoji = "🎲"
                possible = self.config["POSSIBLE_VALUES"][emoji]
            values = set()
            try:
                for val in args[1].split(","):
                    value = int(val)
                    if value in possible:
                        values.add(value)
            except (ValueError, IndexError):
                values.clear()
            try:
                count = int(args[2])
            except (ValueError, IndexError):
                count = 1
            rolled = -1
            done = 0
            chat = message.to_id
            client = message.client
            while True:
                task = client.send_message(chat, file=InputMediaDice(emoji))
                if message:
                    message = (await asyncio.gather(message.delete(), task))[1]
                else:
                    message = await task
                rolled = message.media.value
                logger.debug("Rolled %d", rolled)
                if rolled in values or not values:
                    done += 1
                    message = None
                    if done == count:
                        break
        else:
            try:
                emoji = args[0]
            except IndexError:
                emoji = "🎲"
            await message.reply(file=InputMediaDice(emoji))
