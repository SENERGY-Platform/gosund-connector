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

__all__ = ("Client", )


from .logger import getLogger, logging_levels
from .configuration import dc_conf, EnvVars
import paho.mqtt.client
import logging
import threading


logger = getLogger("mqtt")

mqtt_logger = logging.getLogger("mqtt-client")
mqtt_logger.setLevel(logging_levels.setdefault(dc_conf.Logger.mqtt_level, "debug"))


class Client(threading.Thread):
    def __init__(self, client_id: str, clean_session: str):
        super().__init__(name="mqtt-{}".format(client_id), daemon=True)
        self.__mqtt = paho.mqtt.client.Client(
            client_id=client_id,
            clean_session=clean_session
        )
        self.__mqtt.on_connect = self.__onConnect
        self.__mqtt.on_disconnect = self.__onDisconnect
        self.__mqtt.on_message = self.__onMessage
        self.__mqtt.enable_logger(mqtt_logger)
        self.__mqtt.will_set(dc_conf.Client.lw_topic.format(EnvVars.ModuleID.value), 1, 2)
        self.__discon_count = 0
        self.connectClbk = None
        self.disconnectClbk = None
        self.messageClbk = None

    def run(self) -> None:
        while True:
            try:
                self.__mqtt.connect(dc_conf.MB.host, dc_conf.MB.port, keepalive=dc_conf.Client.keep_alive)
            except Exception as ex:
                logger.error(
                    "could not connect to '{}' on '{}' - {}".format(dc_conf.MB.host, dc_conf.MB.port, ex)
                )
            try:
                self.__mqtt.loop_forever()
            except Exception as ex:
                logger.error("mqtt loop broke - {}".format(ex))

    def __onConnect(self, client, userdata, flags, rc):
        if rc == 0:
            self.__discon_count = 0
            logger.info("connected to '{}'".format(dc_conf.MB.host))
            self.connectClbk()
        else:
            logger.error("could not connect to '{}' - {}".format(dc_conf.MB.host, paho.mqtt.client.connack_string(rc)))

    def __onDisconnect(self, client, userdata, rc):
        if self.__discon_count < 1:
            if rc == 0:
                logger.info("disconnected from '{}'".format(dc_conf.MB.host))
            else:
                logger.warning("disconnected from '{}' unexpectedly".format(dc_conf.MB.host))
            self.__discon_count += 1
            self.disconnectClbk()

    def __onMessage(self, client, userdata, message: paho.mqtt.client.MQTTMessage):
        self.messageClbk(message.topic, message.payload)

    def subscribe(self, topic: str, qos: int) -> None:
        try:
            res = self.__mqtt.subscribe(topic=topic, qos=qos)
            if res[0] is paho.mqtt.client.MQTT_ERR_SUCCESS:
                logger.debug("request subscribe for '{}'".format(topic))
            elif res[0] == paho.mqtt.client.MQTT_ERR_NO_CONN:
                logger.error("not connected")
            else:
                logger.error(paho.mqtt.client.error_string(res[0]).replace(".", "").lower())
        except OSError as ex:
            logger.error(ex)

    def unsubscribe(self, topic: str) -> None:
        try:
            res = self.__mqtt.unsubscribe(topic=topic)
            if res[0] is paho.mqtt.client.MQTT_ERR_SUCCESS:
                logger.debug("request unsubscribe for '{}'".format(topic))
            elif res[0] == paho.mqtt.client.MQTT_ERR_NO_CONN:
                logger.error("not connected")
            else:
                logger.error(paho.mqtt.client.error_string(res[0]).replace(".", "").lower())
        except OSError as ex:
            logger.error(ex)

    def publish(self, topic: str, payload: str, qos: int) -> None:
        try:
            msg_info = self.__mqtt.publish(topic=topic, payload=payload, qos=qos, retain=False)
            if msg_info.rc == paho.mqtt.client.MQTT_ERR_SUCCESS:
                logger.debug("publish '{}' - (q{}, m{})".format(payload, qos, msg_info.mid))
            elif msg_info.rc == paho.mqtt.client.MQTT_ERR_NO_CONN:
                logger.error("not connected")
            else:
                logger.error(paho.mqtt.client.error_string(msg_info.rc).replace(".", "").lower())
        except (ValueError, OSError) as ex:
            logger.error(ex)
