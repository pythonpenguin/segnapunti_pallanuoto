""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 03/08/25

"""

import ujson as json
import network
import time
import machine

from umqtt.robust import MQTTClient


class Display(object):

    def __init__(self, *pins):
        self.pins = [machine.Pin(_x, machine.Pin.OUT) for _x in pins]
        self.sirena = machine.Pin(16, machine.Pin.OUT)
        self.last = time.time_ns()

    def set_value(self, val):
        for _x in range(4):
            self.pins[_x].value((val >> _x) & 1)

    def set_sirena(self, val):
        self.sirena.value(val)


class PnCremaMqtt(MQTTClient):

    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0, ssl=None, ssl_params={},connection_params={}):
        super().__init__(client_id, server, port, user, password, keepalive, ssl, ssl_params)
        self._connection_param = connection_params
        self.topics = {b"display/tempo": self._mostra_numero,
                       b"display/sirena": self._stato_sirena}
        self.nm = network.WLAN(network.STA_IF)
        self.set_callback(self._dispatch)
        self._display = Display(12, 14, 27, 26)
        self._sirena = machine.Pin(16, machine.Pin.OUT)
        self._is_connected_to_server = False

    def connect(self, clean_session=False, timeout=None):
        self.crea_connessione_rete()
        try:
            super().connect(clean_session, timeout)
        except OSError as error:
            self._is_connected_to_server = False
            return False
        self._connection_ready()
        self._is_connected_to_server = True
        return True

    def subscribe_all_topic(self):
        for topic in self.topics:
            self.subscribe(topic, qos=1)

    def reconnect(self):
        self._is_connected_to_server = False
        self.crea_connessione_rete()
        try:
            super().reconnect()
        except OSError as error:
            self._is_connected_to_server = False
            return False
        self._connection_ready()
        self._is_connected_to_server = True
        return True

    def crea_connessione_rete(self):
        if self._is_connected_to_server:
            return
        self._reset_connessione()

        if self.nm.isconnected():
            self.nm.disconnect()
            time.sleep(1)
        while not self.is_connected():
            if not self._cerca_ssid():
                self._on_connection()
                continue
            try:
                self.nm.connect(self._connection_param["ssid"], self._connection_param["password"])
            except OSError:
                self._on_connection()
        print(self.nm.ifconfig())

    def is_connected(self):
        if not self.nm.isconnected():
            return False
        print(self.nm.status())
        return str(self.nm.ifconfig()[0]).startswith(self._connection_param["subnet"])

    def _reset_connessione(self):
        self.nm.active(False)
        time.sleep(1)
        self.nm.active(True)

    def _cerca_ssid(self):
        for _rt in self.nm.scan():
            ssid = _rt[0].decode()
            print("SSID -->{}".format(ssid))
            if ssid == self._connection_param["ssid"]:
                print("SSID match")
                return True
        return False

    def _dispatch(self, topic, msg):
        try:
            self.topics[topic](msg)
        except KeyError:
            pass

    def _mostra_numero(self, msg):
        print("time --> {}".format(msg))
        # self._display.set_value(int(msg))

    def _stato_sirena(self, msg):
        self._display.sirena.value(int(msg))

    def _connection_ready(self):
        self._display.set_value(15)
        self._display.set_sirena(1)

    def _on_connection(self):
        for _x in range(5):
            self._display.set_value(15)
            time.sleep(0.1)
            self._display.set_value(0)
            time.sleep(0.1)

    def check_msg(self, attempts=2):
        try:
            super().check_msg(attempts)
            return True
        except OSError as error:
            return False


with open("/configurazioni/network.json", "r") as fp:
    cfg_net = json.load(fp)
with open("/configurazioni/mqtt.json", "r") as fp:
    cfg_mqtt = json.load(fp)
try:
    client = PnCremaMqtt(cfg_mqtt.get("client_id", "esp32_display"),
                         cfg_mqtt.get("server", "10.42.0.1"), connection_params=cfg_net)
    client.connect()
    client.subscribe_all_topic()
    _count = 0
    while True:
        try:
            client.check_msg()
            time.sleep_us(500)
            _count + 1
            if _count > 10:
                client.ping()
                _count = 0
        except OSError as error:
            client.reconnect()
except OSError as error:
    print(error)
    machine.soft_reset()
except Exception as error:
    print(error)
