"""
   Copyright 2020 InfAI (CC SES)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from ..logger import getLogger
from ..configuration import dc_conf

logger = getLogger(__name__.split(".", 1)[-1])


class GosundSp111:
    def __init__(self):
        self.pending_service_commands = {}
        for service_id in dc_conf.Devices.service_topics:
            self.pending_service_commands[service_id] = []

    def add_pending_command(self, service_id: str, command_id: str):
        self.pending_service_commands[service_id].append(command_id)

    def get_and_reset_commands(self, service_id: str):
        pending_commands = self.pending_service_commands.get(service_id)
        self.pending_service_commands[service_id] = []
        return pending_commands
