""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 03/08/25

"""

import ujson as json
import network
import time
import machine
import urequests
import ubinascii

from umqtt.robust import MQTTClient


class Display(object):

    def __init__(self):
        self.pins = [machine.Pin(_x, machine.Pin.OUT) for _x in (26, 14, 27, 12)]
        self.sirena = machine.Pin(16, machine.Pin.OUT)
        self.units = machine.Pin(33, machine.Pin.OUT)
        self.tens = machine.Pin(25, machine.Pin.OUT)
        self._last_units = -1
        self._last_tens = -1
        self._init_to_99()

    def set_value(self, val):
        self._af_write_tens(val // 10)
        self._af_write_units(val % 10)

    def set_sirena(self, val):
        self.sirena.value(val)
        self._write_units(self._last_units)
        self._write_tens(self._last_tens)
        self._last_units = -1
        self._last_tens = -1

    def _af_write_tens(self, val):
        if self._last_tens == val:
            return
        self._write_tens(val)

    def _write_tens(self, val):
        self._last_tens = val
        self.units.value(1)
        self.tens.value(0)
        self._write(val)

    def _af_write_units(self, val):
        if self._last_units == val:
            return
        self._write_units(val)

    def _write_units(self, val):
        self._last_units = val
        self.tens.value(1)
        self.units.value(0)
        self._write(val)

    def _write(self, val):
        for _x in range(4):
            self.pins[_x].value((val >> _x) & 1)

    def _init_to_99(self):
        self.tens.value(0)
        self.units.value(0)
        self._af_write_tens(9)
        self._af_write_units(9)


class PnCremaMqtt(MQTTClient):
    MSG = "display"
    MSG_TEMPO = "tempo"
    MSG_SIRENA = "sirena"

    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0, ssl=None, ssl_params={},
                 connection_params={}):
        super().__init__(client_id, server, port, user, password, keepalive, ssl, ssl_params)
        self._connection_param = connection_params
        self.topics = {b"display/stato": self._json_msg,
                       b"display/update": self._update_sistema}
        self.nm = network.WLAN(network.STA_IF)
        self.set_callback(self._dispatch)
        self._display = Display()
        self._is_connected_to_server = False
        self._anti_flickering = {self.MSG_TEMPO: -1, self.MSG_SIRENA: -1}

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

    def check_msg(self, attempts=2):
        try:
            super().check_msg(attempts)
            return True
        except OSError as error:
            return False

    def _reset_connessione(self):
        self.nm.active(False)
        time.sleep(1)
        self.nm.active(True)

    def _cerca_ssid(self):
        for _rt in self.nm.scan():
            ssid = _rt[0].decode()
            if ssid == self._connection_param["ssid"]:
                return True
        return False

    def _dispatch(self, topic, msg):
        try:
            self.topics[topic](msg)
        except KeyError:
            pass

    def _mostra_numero(self, msg):
        if msg == self._anti_flickering[self.MSG_TEMPO]:
            return
        self._display.set_value(int(msg))
        self._anti_flickering[self.MSG_TEMPO] = msg

    def _stato_sirena(self, msg):
        if msg == self._anti_flickering[self.MSG_SIRENA]:
            return
        self._display.set_sirena(int(msg))
        self._anti_flickering[self.MSG_SIRENA] = msg

    def _json_msg(self, msg):
        try:
            body = json.loads(msg)[self.MSG]
            self._mostra_numero(body[self.MSG_TEMPO])
            self._stato_sirena(body[self.MSG_SIRENA])
        except KeyError:
            pass

    def _update_sistema(self, msg):
        try:
            info = json.loads(msg)
        except Exception:
            return
        self._try_to_update(info)
        print(str(info))
        self._reboot()

    def _connection_ready(self):
        self._display.set_value(88)

    def _on_connection(self):
        for _x in range(99, 10, -22):
            self._display.set_value(_x)
            time.sleep(0.5)

    def _try_to_update(self, info):
        try:
            url = info["url"]
            position = info["position"]
            try:
                response = urequests.get(url)
                if response.status_code != 200:
                    return False
                with open(position, "w") as f:
                    f.write(response.text)
                return True
            finally:
                response.close()
        except KeyError:
            return False
        except Exception as grave_errore:
            print(grave_errore)
            return False

    def _reboot(self):
        machine.reset()


def make_client_id_unique(cfg):
    cfg["client_id"] = cfg.get("client_id", "") + ubinascii.hexlify(machine.unique_id()).decode()
    return cfg


with open("/configurazioni/network.json", "r") as fp:
    cfg_net = json.load(fp)
with open("/configurazioni/mqtt.json", "r") as fp:
    cfg_mqtt = json.load(fp)

try:
    cfg_mqtt = make_client_id_unique(cfg_mqtt)
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
    print("eseguo un soft reset")
    machine.soft_reset()
except Exception as error:
    print(error)
