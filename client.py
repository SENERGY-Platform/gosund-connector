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

import signal
import sys
import time

from dc.configuration import dc_conf, EnvVars
from dc.handler import Handler
from dc.logger import initLogger, getLogger
from dc.mqtt_client import Client

initLogger(dc_conf.Logger.level)

logger = getLogger("client")


def sigtermHandler(_signo, _stack_frame):
    logger.warning("got SIGTERM - exiting ...")
    sys.exit(0)


def onConnect():
    client.subscribe(dc_conf.Client.event_topic + '/+/' + dc_conf.Devices.lw_topic, 2)


def onDisconnect():
    pass


def onMessage(topic, payload):
    logger.debug("Received message on topic " + topic)
    topic = topic.split("/")
    msg = {
        "message": payload.decode("utf-8")
    }
    if topic[0] == EnvVars.ModuleID.value and topic[1] == dc_conf.Client.response_topic:
        msg["device_id"] = topic[2]
        msg["service_id"] = topic[3]
        handler.handleDeviceResponse(msg)
    else:
        msg["device_id"] = topic[1]
        msg["service_id"] = topic[2]
        if not msg["device_id"].startswith(EnvVars.ModuleID.value):
            return

        handler.handleKnownDevices(msg["device_id"])

        if topic[0] == dc_conf.Client.event_topic:
            handler.handleDeviceLWTMessage(msg)
        elif topic[0] == dc_conf.Client.command_topic:
            handler.handleDeviceCommand(msg)
        elif topic[0] == EnvVars.ModuleID.value and topic[1] == dc_conf.Client.response_topic:
            handler.handleDeviceResponse(msg)
        else:
            logger.error("Received message with no handler on topic " + str(topic))


client = Client(client_id=EnvVars.ModuleID.value, clean_session=dc_conf.Client.clean_session)
client.connectClbk = onConnect
client.disconnectClbk = onDisconnect
client.messageClbk = onMessage

handler = Handler(client)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sigtermHandler)
    signal.signal(signal.SIGINT, sigtermHandler)

    client.start()
    while True:
        time.sleep(10)
