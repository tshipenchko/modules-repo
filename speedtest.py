# -*- coding: future_fstrings -*-

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

# requires: speedtest-cli>=2.1.0

import logging
import speedtest

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(SpeedtestMod())


@loader.tds
class SpeedtestMod(loader.Module):
    """Uses speedtest.net"""
    strings = {"name": "Speedtest",
               "running": "<code>Running speedtest...</code>",
               "results_header": "<b>Speedtest Results:</b>",
               "dl_speed": "<b>Download:</b> <code>{} MiB/s</code>",
               "ul_speed": "<b>Upload:</b> <code>{} MiB/s</code>",
               "ping": "<b>Ping:</b> <code>{} milliseconds</code>"}

    def __init__(self):
        self.name = self.strings["name"]

    async def speedtestcmd(self, message):
        """Tests your internet speed"""
        await utils.answer(message, self.strings["running"])
        args = utils.get_args(message)
        servers = []
        for server in args:
            try:
                servers += [int(server)]
            except ValueError:
                logger.warning("server failed")
        results = await utils.run_sync(self.speedtest, servers)
        ret = self.strings["results_header"] + "\n\n"
        ret += self.strings["dl_speed"].format(round(results["download"] / 2**20, 2)) + "\n"
        ret += self.strings["ul_speed"].format(round(results["upload"] / 2**20, 2)) + "\n"
        ret += self.strings["ping"].format(round(results["ping"], 2)) + "\n"
        await utils.answer(message, ret)

    def speedtest(self, servers):
        speedtester = speedtest.Speedtest()
        speedtester.get_servers(servers)
        speedtester.get_best_server()
        speedtester.download(threads=None)
        speedtester.upload(threads=None)
        return speedtester.results.dict()
