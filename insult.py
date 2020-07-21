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
import random


logger = logging.getLogger(__name__)


@loader.tds
class InsultMod(loader.Module):
    """Кричит на людей"""
    strings = {"name": "Insulter"}

    @loader.unrestricted
    async def insultcmd(self, message):
        """Используйте, когда злитесь"""
        # TODO localisation?
        adjectives_start = ["соленый", "жирный", "ебаный", "говенный", "тупой", "умственно отсталый", "застенчивый", "крохотный"]
        adjectives_mid = ["маленький", "витамино D дефицитный", "идиотский", "невероятно глупый"]
        nouns = ["пиздёныш", "свин", "педофил", "бета самец", "днище-мудила", "даун", "очколиз", "пиздолиз",
                 "ПЕНИС", "залупенец", "желобок", "идиот", "ублюдок", "холостяк", "крип"]
        starts = ["Ты блять", "Ты", "Ты ёбаный", "На самом деле ты мёртвый", "Слушай, ты -",
                  "Что за хрень с тобой, ты"]
        ends = ["!!!!", "!", ""]
        start = random.choice(starts)
        adjective_start = random.choice(adjectives_start)
        adjective_mid = random.choice(adjectives_mid)
        noun = random.choice(nouns)
        end = random.choice(ends)
        insult = start + " " + adjective_start + " " + adjective_mid + (" " if adjective_mid else "") + noun + end
        logger.debug(insult)
        await utils.answer(message, insult)
