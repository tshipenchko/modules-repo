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

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(DiceMod())


@loader.tds
class DiceMod(loader.Module):
    """Dice"""
    strings = {"name": "Dice",
               "dice_emoji_cfg_doc": "The emoji to be sent to Telegram as a dice. Can currently be either 🎲 or 🎯"}

    def __init__(self):
        self.config = loader.ModuleConfig("DICE_EMOJI", "🎲", lambda: self.strings["dice_emoji_cfg_doc"])

    def config_complete(self):
        self.name = self.strings["name"]

    async def dicecmd(self, message):
        """Rolls a die (optionally with the specified value)"""
        args = utils.get_args(message)
        values = set()
        try:
            for val in args[0].split(","):
                value = int(val)
                if value >= 1 and value <= 6:
                    values.add(value)
        except (ValueError, IndexError):
            values.clear()
        try:
            count = int(args[1])
        except (ValueError, IndexError):
            count = 1
        rolled = -1
        done = 0
        chat = message.to_id
        client = message.client
        while True:
            task = client.send_message(chat, file=InputMediaDice(self.config["DICE_EMOJI"]))
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
