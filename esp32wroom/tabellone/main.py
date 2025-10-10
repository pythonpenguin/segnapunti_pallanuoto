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
        self.pins = [machine.Pin(_x, machine.Pin.OUT) for _x in (26,14,27,12)]
        self.sirena = machine.Pin(16, machine.Pin.OUT)
        self.second_units = machine.Pin(33, machine.Pin.OUT)
        self.second_tens = machine.Pin(25, machine.Pin.OUT)
        self.minutes = machine.Pin(13, machine.Pin.OUT)
        self.home_units = machine.Pin(18, machine.Pin.OUT)
        self.home_tens = machine.Pin(5, machine.Pin.OUT)
        self.away_units = machine.Pin(21, machine.Pin.OUT)
        self.away_tens = machine.Pin(19, machine.Pin.OUT)
        self.period = machine.Pin(15, machine.Pin.OUT)
        self.led = machine.Pin(23, machine.Pin.OUT)
        self._last_period = -1
        self._last_goal_home = -1
        self._last_goal_away = -1
        self._last_time_min = -1
        self._last_time_sec = -1
        self._init_to_99()

    def af_refresh_periodo(self,value):
        if self._last_period != value:
            self._last_period = value
        self._write_period(value)

    def af_refresh_gol_casa(self,value):
        if self._last_goal_home != value:
            self._last_goal_home = value
        self._write_home_tens(value // 10)
        self._write_home_units(value % 10)

    def af_refresh_gol_trasferta(self,value):
        if self._last_goal_away != value:
            self._last_goal_away = value
        self._write_away_tens(value // 10)
        self._write_away_units(value % 10)

    def af_refresh_timer_minuti(self,value):
        if self._last_time_min != value:
            self._last_time_min = value
        self._write_minutes(value)

    def af_refresh_timer_secondi(self,value):
        if self._last_time_sec != value:
            self._last_time_sec = value
        self._write_second_tens(value // 10)
        self._write_second_units(value % 10)

    def set_value(self, val):
        self._write_second_tens(val // 10)
        self._write_second_units(val % 10)
        self._write_minutes(val//10)
        self._write_period(val%10)
        self._write_home_tens(val//10)
        self._write_home_units(val%10)
        self._write_away_tens(val//10)
        self._write_away_units(val%10)

    def set_sirena(self, val):
        self.sirena.value(val)

    def _reset_table(self):
        self.second_units.value(1)
        self.second_tens.value(1)
        self.minutes.value(1)
        self.home_units.value(1)
        self.home_tens.value(1)
        self.away_units.value(1)
        self.away_tens.value(1)
        self.period.value(1)

    def _write_second_tens(self, val):
        self._reset_table()
        self.second_tens.value(0)
        self._write(val)

    def _write_second_units(self, val):
        self._reset_table()
        self.second_units.value(0)
        self._write(val)

    def _write_minutes(self, val):
        self._reset_table()
        self.minutes.value(0)
        self._write(val)

    def _write_home_units(self, val):
        self._reset_table()
        self.home_units.value(0)
        self._write(val)

    def _write_home_tens(self, val):
        self._reset_table()
        self.home_tens.value(0)
        self._write(val)

    def _write_away_units(self, val):
        self._reset_table()
        self.away_units.value(0)
        self._write(val)

    def _write_away_tens(self, val):
        self._reset_table()
        self.away_tens.value(0)
        self._write(val)

    def _write_period(self, val):
        self._reset_table()
        self.period.value(0)
        self._write(val)

    def _write(self,val):
        for _x in range(4):
            self.pins[_x].value((val >> _x) & 1)

    def _init_to_99(self):
        self.second_tens.value(0)
        self.second_units.value(0)
        self.minutes.value(0)
        self.period.value(0)
        self.home_units.value(0)
        self.home_tens.value(0)
        self.away_units.value(0)
        self.away_tens.value(0)
        self._write_second_tens(9)
        self._write_second_units(9)
        self._write_minutes(9)
        self._write_period(9)
        self._write_home_tens(9)
        self._write_home_units(9)
        self._write_away_tens(9)
        self._write_away_units(9)

class PnCremaMqtt(MQTTClient):

    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0, ssl=None, ssl_params={},connection_params={}):
        super().__init__(client_id, server, port, user, password, keepalive, ssl, ssl_params)
        self._connection_param = connection_params
        self.topics = {b"tabellone/stato": self._json_msg,
                       b"tabellone/update": self._update_sistema}
        self.nm = network.WLAN(network.STA_IF)
        self.set_callback(self._dispatch)
        self._display = Display()
        self._is_connected_to_server = False
        self._current_status = {}

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

    def _json_msg(self, msg):
        try:
            body = json.loads(msg)
            if self._current_status.get("periodo")!=body["periodo"]:
                self._refresh_periodo(body["periodo"])
            if self._current_status.get("gol_casa") != body["gol_casa"]:
                self._refresh_gol_casa(body["gol_casa"])
            if self._current_status.get("gol_trasferta") != body["gol_trasferta"]:
                self._refresh_gol_trasferta(body["gol_trasferta"])
            self._refresh_timer_gioco(body["tempo_gioco"])
            self._current_status = body
        except KeyError:
            pass

    def _refresh_periodo(self,value):
        self._display.af_refresh_periodo(int(value))

    def _refresh_gol_casa(self,value):
        self._display.af_refresh_gol_casa(int(value))

    def _refresh_gol_trasferta(self,value):
        self._display.af_refresh_gol_trasferta(int(value))

    def _refresh_timer_gioco(self,value):
        _ct= self._current_status.get("tempo_gioco",{})
        if _ct.get("min")!=value["min"]:
            self._display.af_refresh_timer_minuti(int(value["min"]))
        if _ct.get("sec") != value["sec"]:
            self._display.af_refresh_timer_secondi(int(value["sec"]))

    def _update_sistema(self,msg):
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
        for _x in range(99,10,-22):
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
    cfg["client_id"] = cfg.get("client_id","") + ubinascii.hexlify(machine.unique_id()).decode()
    return cfg

with open("/configurazioni/network.json", "r") as fp:
    cfg_net = json.load(fp)
with open("/configurazioni/mqtt.json", "r") as fp:
    cfg_mqtt = json.load(fp)

try:
    cfg_mqtt=make_client_id_unique(cfg_mqtt)
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