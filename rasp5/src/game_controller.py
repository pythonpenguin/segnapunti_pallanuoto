""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 08/08/25

"""
import asyncio

import json
import math
from paho.mqtt import client as mqtt


class GameController(object):
    CANALE_DISPLAY = "display"
    SIRENA = "{}/sirena".format(CANALE_DISPLAY)
    TEMPO_GIOCO = "{}/tempo".format(CANALE_DISPLAY)

    CANALE_TABELLONE = "tabellone"
    GOL_CASA = "{}/gol_casa".format(CANALE_TABELLONE)
    PERIODO = "{}/periodo".format(CANALE_TABELLONE)
    TEMPO_PERIODO = "{}/tempo".format(CANALE_TABELLONE)
    REFRESH_TABELLONE = "{}/stato".format(CANALE_TABELLONE)
    REFRESH_GLOBALE = "stato"

    def __init__(self, game_configurator, mqtt_host="localhost", keepalive=5):
        """

        :param game_configure.GameConfigure game_configurator:
        :param mqtt_host:
        :param keepalive:
        """
        self.game_config = game_configurator
        self.mqtt_host = mqtt_host
        self.mqtt_keepalive = keepalive
        self.client = mqtt.Client()

        self.tempo_periodo = 0  # in secondi
        self.tempo_possesso_palla = 0
        self.tempo_timeout_chiamato_squadre = 0
        self.tempo_pausa_periodi_1_3 = 0
        self.tempo_pause_meta_partita = 0

        self.periodo = 0
        self.max_periodi = 0
        self.score_home = 0
        self.score_away = 0
        self.sirena = 0
        self.timeout_home = 0
        self.timeout_away = 0
        self.max_timeout=0

        self.game_running = False
        self.timeout_running = False
        self._current_time_out = 0
        self.tempo_refresh = 0.25
        self._game_time_last_update = asyncio.get_event_loop().time()
        self._task_sirena = None
        self._task_timeout = None

        self.reset_match()

    def reset_match(self):
        self.tempo_periodo = self.game_config.tempo_periodo()  # in secondi
        self.tempo_possesso_palla = self.game_config.tempo_gioco()
        self.tempo_timeout_chiamato_squadre = self.game_config.tempo_timeout()
        self.tempo_pausa_periodi_1_3 = self.game_config.tempo_fine_periodo()
        self.tempo_pause_meta_partita = self.game_config.tempo_meta_partita()
        self.max_periodi = self.game_config.periodi_gioco()
        self.max_timeout = self.game_config.numero_timeouts()
        self.timeout_home=0
        self.timeout_away=0
        self.periodo = 1
        self.score_home = 0
        self.score_away = 0
        self.sirena = 0
        self.game_running = False
        self.timeout_running = False
        self.tempo_refresh = 0.25
        self._game_time_last_update = asyncio.get_event_loop().time()
        self._task_sirena = None
        self._current_time_out = 0

    def connect_to_broker(self):
        if self.client.is_connected():
            return
        self.client.connect(self.mqtt_host, keepalive=self.mqtt_keepalive)

    def publish(self, topic, msg, retain=False):
        self.client.publish(topic, msg, retain=retain)

    def start(self):
        self.game_running = True

    def stop(self):
        if self.game_running:
            self.game_running = False

    def reset_possesso_palla(self):
        self.tempo_possesso_palla = self.game_config.tempo_gioco()

    def reset_tempo_periodo(self):
        self.tempo_periodo = self.game_config.tempo_periodo()

    def force_tempo_periodo(self,value):
        """

        :param int value:
        """
        self.tempo_periodo = min(value, self.game_config.tempo_periodo())

    def set_tempo_aggiuntivo(self):
        if self.tempo_possesso_palla < self.game_config.tempo_aggiuntivo():
            self.tempo_possesso_palla = self.game_config.tempo_aggiuntivo()

    def next_period(self):
        self.periodo += 1
        self.periodo = min(self.periodo, self.max_periodi)

    def prev_period(self):
        self.periodo -= 1
        self.periodo = max(self.periodo,1)

    def goal_casa_piu(self):
        self.score_home += 1
        self.score_home = min(self.score_home, 99)

    def goal_casa_meno(self):
        self.score_home -= 1
        self.score_home = max(0, self.score_home)

    def goal_tasferta_piu(self):
        self.score_away += 1
        self.score_away = min(self.score_away, 99)

    def goal_tasferta_meno(self):
        self.score_away -= 1
        self.score_away = max(0, self.score_away)

    def timeout_casa_piu(self):
        self.timeout_home += 1
        self.timeout_home = min(self.timeout_home,self.max_timeout)

    def timeout_casa_meno(self):
        self.timeout_home -= 1
        self.timeout_home = max(self.timeout_home,0)

    def timeout_trasferta_piu(self):
        self.timeout_away += 1
        self.timeout_away = min(self.timeout_away,self.max_timeout)

    def timeout_trasferta_meno(self):
        self.timeout_away -= 1
        self.timeout_away = max(self.timeout_away,0)

    def timeout_set_chiamato_squadre(self):
        self._current_time_out = self.tempo_timeout_chiamato_squadre

    def timeout_set_pausa_13(self):
        self._current_time_out = self.tempo_pausa_periodi_1_3

    def timeout_set_half_time(self):
        self._current_time_out = self.tempo_pause_meta_partita

    def sirena_on(self):
        self.sirena = 1

    def sirena_off(self):
        self.sirena = 0

    def timeout_start(self):
        if self.game_running:
            return
        if not self._current_time_out:
            return
        self.timeout_running = True
        self._task_timeout = asyncio.create_task(self._timeout_loop())

    async def _timeout_loop(self):
        last = asyncio.get_event_loop().time()
        while self._current_time_out > 0.0:
            now = asyncio.get_event_loop().time()
            delta = now - last
            last = now
            self._current_time_out -= delta
            await asyncio.sleep(0.05)
        self._current_time_out = 0.0
        self.timeout_attivo = False
        self.sirena_on()

    def timeout_reset(self):
        if self._task_timeout:
            self._task_timeout.cancel()
        self.timeout_attivo = False
        self._current_time_out = 0.0

    def timeout_stop(self):
        pass

    async def refresh(self):
        while True:
            stato = {"tabellone": {"gol_casa": self.score_home,
                                   "gol_trasferta": self.score_away,
                                   "periodo": self.periodo,
                                   "tempo_gioco": self._min_sec_fmt(self.tempo_periodo),
                                   "timeout_casa":self.timeout_home,
                                   "timeout_trasferta": self.timeout_away,
                                   "timeout_clock":self._min_sec_fmt(self._current_time_out),
                                   },
                     "display": {"tempo": self._formato_tempo_possesso_palla(), "sirena": self.sirena}}
            self.publish(self.REFRESH_GLOBALE, json.dumps(stato))
            await asyncio.sleep(self.tempo_refresh)

    async def tempo_gioco_loop(self):
        _tempo_sleep = 0.02
        while True:
            now = asyncio.get_event_loop().time()
            if self.game_running and self.tempo_periodo > 0:
                delta = now - self._game_time_last_update
                self.tempo_periodo -= delta
                self.tempo_possesso_palla -= delta
                if self.tempo_periodo <= 0:
                    self.tempo_periodo = 0
                    self.game_running = False
                    self.sirena_on()
                if self.tempo_possesso_palla <= 0:
                    self.game_running = False
                    self.reset_possesso_palla()
                    self.sirena_on()
            self._game_time_last_update = now
            self._check_stato_sirena()
            await asyncio.sleep(_tempo_sleep)

    async def timeout_loop(self):
        _tempo_sleep = 0.02
        while True:
            now = asyncio.get_event_loop().time()
            if not self.game_running and self.timeout_running and self.tempo_periodo > 0:
                delta = now - self._game_time_last_update
                self.tempo_periodo -= delta
                self.tempo_possesso_palla -= delta
                if self.tempo_periodo <= 0:
                    self.tempo_periodo = 0
                    self.game_running = False
                    self.sirena_on()
                if self.tempo_possesso_palla <= 0:
                    self.game_running = False
                    self.reset_possesso_palla()
                    self.sirena_on()
            self._game_time_last_update = now
            self._check_stato_sirena()
            await asyncio.sleep(_tempo_sleep)

    def _check_stato_sirena(self):
        if self.sirena and self._task_sirena is None:
            self._task_sirena = asyncio.create_task(self._sirena_off())

    async def _sirena_off(self):
        await asyncio.sleep(2)
        self.sirena = 0
        self._task_sirena = None

    def _min_sec_fmt(self, timing):
        minuti, secondi = divmod(int(math.ceil(timing)), 60)
        return {"min": f"{minuti:02}", "sec": f"{secondi:02}"}

    def _formato_tempo_possesso_palla(self):
        return int(math.ceil(self.tempo_possesso_palla))

    def update_display(self):  # da testare
        self.stop()
        self.publish("display/tempo", str(44))
        jts = json.dumps({"url": "http://10.42.0.1/main.py", "position": "main.py"})
        self.publish("display/update", jts)
