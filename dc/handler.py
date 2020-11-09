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

import json

from dc.configuration import EnvVars, dc_conf
from dc.devices.gosundsp111 import GosundSp111
from dc.logger import getLogger
from dc.mqtt_client import Client

logger = getLogger("handler")


class DeviceState:
    online = "online"
    offline = "offline"


class Method:
    set = "set"
    delete = "delete"


class Handler:
    def __init__(self, client: Client):
        self.client = client
        self.gosunds = {}

    def handleKnownDevices(self, device_id: str):
        if device_id not in self.gosunds:
            logger.info("Adding " + device_id + " to list of known devices")
            for service in dc_conf.Devices.service_topics:
                self.client.subscribe(dc_conf.Client.command_topic + '/' + device_id + '/' + service, 2)
                self.client.subscribe(
                    EnvVars.ModuleID.value + "/" + dc_conf.Client.response_topic + '/' + device_id + '/' + service,
                    2)
            self.gosunds[device_id] = GosundSp111()

    def handleDeviceLWTMessage(self, msg):
        data = {
            "name": msg["device_id"][len(EnvVars.ModuleID.value) + 1:],  # Remove "gosund-" or similar
            "device_type": dc_conf.Devices.type,
        }
        state = None
        if msg["message"] == "Online":
            state = DeviceState.online
        elif msg["message"] == "Offline":
            state = DeviceState.offline
        self.setDevice(msg["device_id"], data, Method.set, state)

    def handleDeviceResponse(self, msg):
        logger.info(msg["device_id"] + " responded with " + msg["message"])
        response = {
            "data": msg["message"]
        }
        for command_id in self.gosunds[msg["device_id"]].get_and_reset_commands(
            msg["service_id"]):  # Answer every pending service command
            response["command_id"] = command_id
            self.client.publish(dc_conf.Client.response_topic + '/' + msg["device_id"] + '/' + msg["service_id"],
                                json.dumps(response).replace("'", "\""), 2)

    def handleDeviceCommand(self, msg):
        jsonMsg = json.loads(msg["message"])
        logger.info("Setting " + msg["device_id"] + " on Service " + msg["service_id"] + " to " + jsonMsg["data"])
        self.client.publish(
            EnvVars.ModuleID.value + '/' + dc_conf.Client.command_topic + '/' + msg["device_id"] + '/'
            + msg["service_id"], jsonMsg["data"], 2)
        self.gosunds[msg["device_id"]].add_pending_command(msg["service_id"], jsonMsg["command_id"])

    def setDevice(self, device_id: str, data: dict, method: str, state=None):
        logger.info("Device " + device_id + " is now " + state)
        msg = {
            "method": method,
            "device_id": device_id,
            "data": {
                "name": data["name"].replace("_", " "),
                "state": state,
                "device_type": data["device_type"]
            }
        }
        self.client.publish("{}/{}".format(dc_conf.Client.device_topic, EnvVars.ModuleID.value), json.dumps(msg),
                            2)
