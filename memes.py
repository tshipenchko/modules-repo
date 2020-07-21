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

# requires: pyfiglet

from .. import loader, utils
import logging
import random
import re
from pyfiglet import Figlet, FigletFont, FontNotFound

logger = logging.getLogger(__name__)


@loader.tds
class MockMod(loader.Module):
    """ВыСмЕиВаНиЕ лЮдЕй))0)"""
    strings = {"name": "Memes",
               "mock_args": "<b>ОтВеТьТе На СоОбЩеНиЕ, чТоБы ВыСмЕяТь ЕгО (иЛи ВвЕдИтЕ сОоБщЕнИе ПоСлЕ кОмАнДы)</b>",
               "figlet_args": "<b>Укажите шрифт и текст для рендеринга с помощью figlet</b>",
               "no_font": "<b>Шрифт не найден</b>",
               "uwu_args": "<b>Мне нужен текст для nyeko.</b>",
               "clap_args": "<b>Ха-ха, я не хлопаю без текста!",
               "vapor_args": "<b>Вы не можете ничего испарять, не так ли?</b>",
               "shout_args": "<b>Вы не можете кричать без текста.</b>"}

    @loader.unrestricted
    async def mockcmd(self, message):
        """Используется в ответ на другое сообщение или как .mock <текст>"""
        text = utils.get_args_raw(message.message)
        if len(text) == 0:
            if message.is_reply:
                text = (await message.get_reply_message()).message
            else:
                await utils.answer(message, self.strings("mock_args", message))
                return
        text = list(text)
        n = 0
        rn = 0
        for c in text:
            if n % 2 == random.randint(0, 1):
                text[rn] = c.upper()
            else:
                text[rn] = c.lower()
            if c.lower() != c.upper():
                n += 1
            rn += 1
        text = "".join(text)
        logger.debug(text)
        await utils.answer(message, utils.escape_html(text))

    @loader.unrestricted
    async def figletcmd(self, message):
        """.figlet <шрифт> <текст>"""
        # We can't localise figlet due to a lack of fonts
        args = utils.get_args(message)
        if len(args) < 2:
            await utils.answer(message, self.strings("figlet_args", message))
            return
        text = " ".join(args[1:])
        mode = args[0]
        if mode == "random":
            mode = random.choice(FigletFont.getFonts())
        try:
            fig = Figlet(font=mode, width=30)
        except FontNotFound:
            await utils.answer(message, self.strings("no_font", message))
            return
        await utils.answer(message, "<code>\u206a" + utils.escape_html(fig.renderText(text)) + "</code>")

    @loader.unrestricted
    @loader.ratelimit  # TODO switch away from regex so this isn't a risk
    async def uwucmd(self, message):
        """Используица в отвтт на дрггое соопщенние или типааа .uwu <текст>"""
        text = utils.get_args_raw(message.message)
        if not text:
            if message.is_reply:
                text = (await message.get_reply_message()).message
            else:
                await utils.answer(message, self.strings("uwu_args", message))
                return
        reply_text = re.sub(r"(r|l)", "w", text)
        reply_text = re.sub(r"(R|L)", "W", reply_text)
        reply_text = re.sub(r"n([aeiouAEIOU])", r"ny\1", reply_text)
        reply_text = re.sub(r"N([aeiouAEIOU])", r"Ny\1", reply_text)
        reply_text = reply_text.replace("ove", "uv")
        await utils.answer(message, utils.escape_html(reply_text))

    @loader.unrestricted
    @loader.ratelimit  # TODO switch away from regex as above
    async def clapcmd(self, message):
        """Используется в ответ на другое сообщение или как .clap <текст>"""
        text = utils.get_args_raw(message.message)
        if not text:
            if message.is_reply:
                text = (await message.get_reply_message()).message
            else:
                await utils.answer(message, self.strings("clap_args", message))
                return
        clapped_text = re.sub(" ", " 👏 ", text)
        reply_text = "👏 {} 👏".format(clapped_text)
        await utils.answer(message, utils.escape_html(reply_text))

    @loader.unrestricted
    async def vaporcmd(self, message):
        """Используется в ответ на другое сообщение или как .vapor <текст>"""
        text = utils.get_args_raw(message.message)
        if not text:
            if message.is_reply:
                text = (await message.get_reply_message()).message
            else:
                await utils.answer(message, self.strings("vapor_args", message))
                return
        reply_text = list()
        for char in text:
            if 0x21 <= ord(char) <= 0x7F:
                reply_text.append(chr(ord(char) + 0xFEE0))
            elif ord(char) == 0x20:
                reply_text.append(chr(0x3000))
            else:
                reply_text.append(char)
        vaporized_text = "".join(reply_text)
        await utils.answer(message, vaporized_text)

    @loader.unrestricted
    async def shoutcmd(self, message):
        """.shout <текст> делает текст массивным"""
        text = utils.get_args_raw(message)
        if not text:
            if message.is_reply:
                text = (await message.get_reply_message()).message
            else:
                await utils.answer(message, self.strings("shout_args", message))
                return
        result = " ".join(text) + "\n" + "\n".join(sym + " " * (pos * 2 + 1) + sym for pos, sym in enumerate(text[1:]))
        await utils.answer(message, "<code>" + utils.escape_html(result) + "</code>")
