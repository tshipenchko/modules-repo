#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors
#    Copyright (C) 2018-2020 OrangeFox Recovery

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

import aiohttp

from .. import loader, utils


def register(cb):
    cb(OrangeFoxMod())


@loader.tds
class OrangeFoxMod(loader.Module):
    """Integration with the OrangeFox Recovery API to fetch supported devices"""

    strings = {"name": "OrangeFox Recovery",
               "api_host_cfg_doc": "The API endpoint to query for device information",
               "list_devices_stable_header": "<b>List of supported devices with stable releases:</b>",
               "no_such_device": "<b>No such device is found!</b>",
               "header_stable": "<b>Latest OrangeFox Recovery stable release</b>",
               "device_info": "\n<b>Device:</b> {} (<code>{}</code>)",
               "version": "\n<b>Version:</b> <code>{}</code>",
               "release_date": "\n<b>Release date:</b> {}",
               "maintained_1": "\n<b>Maintainer:</b> {}, Maintained",
               "maintained_2": "\n<b>Maintainer:</b> {}, Maintained without having device on hands",
               "maintained_3": "\n⚠️ <b>Not maintained!</b> Previous maintainer: {}",
               "file": "\n<b>File:</b> <code>{}</code>: {}",
               "file_md5": "\n<b>File MD5:</b> <code>{}</code>",
               "build_notes": "\n\n<b>Build notes:</b>\n",
               "download_link_text": "Download",
               "mirror_link_text": "Mirror"}

    def __init__(self):
        self.config = loader.ModuleConfig("API_HOST", "https://api.orangefox.tech/",
                                          lambda m: self.strings("api_host_cfg_doc", m))
        self.session = aiohttp.ClientSession()

    async def ofoxcmd(self, message):
        """Get's last OrangeFox releases"""
        args = utils.get_args(message)
        devices = await self._send_request("list_devices")
        if args:
            codename = args[0].lower()
            if codename not in [a["codename"] for a in devices]:
                await utils.answer(message, self.strings("no_such_device", message))
                return

            release = await self._send_request("last_stable_release", codename)
            device = await self._send_request("details", codename)

            text = self.strings("header_stable", message)
            text += self.strings("device_info", message).format(device["fullname"], device["codename"])
            text += self.strings("version", message).format(release["version"])
            text += self.strings("release_date", message).format(release["date"])
            text += self.strings("version", message).format(release["version"])

            if device["maintained"] in (1, 2, 3):
                text += self.strings("maintained_" + str(device["maintained"]), message).format(device["maintainer"])

            text += self.strings("file", message).format(release["file_name"], release["size_human"])
            text += self.strings("file_md5", message).format(release["md5"])

            if "notes" in release:
                text += self.strings("build_notes", message)
                text += release["notes"]

            text += "\n<a href=\"{}\">{}</a>".format(release["url"], self.strings("download_link_text", message))
            if "sf" in release:
                text += " | <a href=\"{}\">{}</a>".format(release["sf"]["url"],
                                                          self.strings("mirror_link_text", message))

            await utils.answer(message, text)
        else:
            text = self.strings("list_devices_stable_header", message)
            codenames = await self._send_request("available_stable_releases")

            for device in devices:
                if device["codename"] not in codenames:
                    continue

                text += "\n- {} (<code>{}</code>)".format(device["fullname"], device["codename"])

            await utils.answer(message, text)

    async def _send_request(self, *endpoint):
        async with self.session.get(self.config["API_HOST"] + "/" + ("/".join(endpoint))) as response:
            return await response.json()
