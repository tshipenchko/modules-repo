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

import logging
import requests
import asyncio

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(TransferShMod())


def sgen(agen, loop):
    while True:
        try:
            yield utils.run_async(loop, agen.__anext__())
        except StopAsyncIteration:
            return


@loader.tds
class TransferShMod(loader.Module):
    """Upload to and from transfer.sh"""
    strings = {"name": "transfer.sh support",
               "up_cfg_doc": "URL to upload the file to.",
               "file_plox": "<code>Provide a file to upload</code>",
               "uploading": "<code>Uploading...</code>",
               "uploaded": "<a href={}>Uploaded!</a>"}

    def __init__(self):
        self.config = loader.ModuleConfig("UPLOAD_URL", "https://transfer.sh/{}", lambda: self.strings["up_cfg_doc"])
        self.name = self.strings["name"]

    async def uploadshcmd(self, message):
        """Uploads to transfer.sh"""
        if message.file:
            msg = message
        else:
            msg = (await message.get_reply_message())
        doc = msg.media
        if doc is None:
            await utils.answer(message, self.strings["file_plox"])
            return
        doc = message.client.iter_download(doc)
        logger.debug("begin transfer")
        await utils.answer(message, self.strings["uploading"])
        r = await utils.run_sync(requests.put, self.config["UPLOAD_URL"].format(msg.file.name),
                                 data=sgen(doc, asyncio.get_event_loop()))
        logger.debug(r)
        r.raise_for_status()
        logger.debug(r.headers)
        await utils.answer(message, self.strings["uploaded"].format(r.text))
