""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 08/08/25

"""
import asyncio
import sys
import math

import json
from paho.mqtt import client as mqtt


class GameController(object):
    CANALE_DISPLAY = "display"
    CANALE_DISPLAY_STATO = "{}/stato".format(CANALE_DISPLAY)

    CANALE_TABELLONE = "tabellone"
    CANALE_TABELLONE_STATO = "{}/stato".format(CANALE_TABELLONE)
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

        self.possesso_palla_enable=True

        self.game_running = False
        self.timeout_running = False
        self._current_time_out = 0
        self.default_tempo_refresh=0.25
        self._current_tempo_refresh = self.default_tempo_refresh
        self._game_time_last_update = asyncio.get_event_loop().time()
        self._task_sirena = None
        self._task_timeout = None
        self._loop_enable=True
        self.reset_match()

    def reset_match(self):
        self.tempo_periodo = self.game_config.tempo_periodo()  # in secondi
        self.tempo_possesso_palla = self.game_config.tempo_gioco()
        self.tempo_timeout_chiamato_squadre = self.game_config.tempo_timeout()
        self.tempo_pausa_periodi_1_3 = self.game_config.tempo_fine_periodo()
        self.tempo_pause_meta_partita = self.game_config.tempo_meta_partita()
        self.max_periodi = self.game_config.periodi_gioco()
        self.max_timeout = self.game_config.numero_timeouts()
        self.possesso_palla_enable = self.game_config.tempo_effettivo()
        self.timeout_home=0
        self.timeout_away=0
        self.periodo = 1
        self.score_home = 0
        self.score_away = 0
        self.sirena = 0
        self.game_running = False
        self.timeout_running = False
        self.default_tempo_refresh = 0.25
        self._current_tempo_refresh = self.default_tempo_refresh
        self._game_time_last_update = asyncio.get_event_loop().time()
        self._task_sirena = None
        self._current_time_out = 0

    def shutdown(self):
        self.timeout_reset()
        self._loop_enable=False

    def connect_to_broker(self):
        if self.client.is_connected():
            return
        self.client.connect(self.mqtt_host, keepalive=self.mqtt_keepalive)

    def publish(self, topic, msg, retain=False):
        self.client.publish(topic, msg, retain=retain)

    def load_categoria(self, categoria):
        self.game_config.set_categoria(categoria)
        self.reset_match()

    def label_categoria(self):
        return self.game_config.get_label_categoria()

    def start(self):
        self.game_running = True

    def stop(self):
        if self.game_running:
            self.game_running = False

    def reset_possesso_palla(self):
        self.tempo_possesso_palla = self.game_config.tempo_gioco()

    def reset_tempo_periodo(self):
        if not self.game_running:
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
        if self.game_running or self.timeout_running:
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
        self.timeout_running = False
        self.sirena_on()

    def timeout_reset(self):
        if self._task_timeout:
            self._task_timeout.cancel()
        self.timeout_running = False
        self._current_time_out = 0.0

    def timeout_stop(self):
        pass

    async def refresh(self):
        while self._loop_enable:
            stato = {"tabellone": {"gol_casa": self.score_home,
                                   "gol_trasferta": self.score_away,
                                   "periodo": self.periodo,
                                   "tempo_gioco": self._min_sec_fmt(self.tempo_periodo),
                                   "timeout_casa":self.timeout_home,
                                   "timeout_trasferta": self.timeout_away,
                                   "timeout_clock":self._min_sec_fmt(self._current_time_out),
                                   "sirena": self.sirena
                                   },
                     "display": {"tempo": self._formato_tempo_possesso_palla(), "sirena": self.sirena}}
            self.publish(self.CANALE_DISPLAY_STATO, json.dumps(stato["display"]))
            self.publish(self.CANALE_TABELLONE_STATO, json.dumps(stato["tabellone"]))
            self.publish(self.REFRESH_GLOBALE, json.dumps(stato))
            if 0<self.tempo_periodo<1.0 or 0<self._current_time_out<1.0:
                self._current_tempo_refresh=0.1
            else:
                self._current_tempo_refresh=self.default_tempo_refresh
            await asyncio.sleep(self._current_tempo_refresh)

    async def tempo_gioco_loop(self):
        _tempo_sleep = 0.01
        while self._loop_enable:
            now = asyncio.get_event_loop().time()
            if self.game_running and self.tempo_periodo > 0:
                delta = now - self._game_time_last_update
                self.tempo_periodo -= delta
                if self.tempo_periodo <= 0:
                    self.tempo_periodo = 0
                    self.game_running = False
                    self.sirena_on()
                if self.possesso_palla_enable:
                    self.tempo_possesso_palla -= delta
                    if self.tempo_possesso_palla <= 0:
                        self.game_running = False
                        self.reset_possesso_palla()
                        self.sirena_on()
            self._game_time_last_update = now
            self._check_stato_sirena()
            await asyncio.sleep(_tempo_sleep)

    async def input_loop(self):
        while self._loop_enable:
            cmd = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            cmd = cmd.strip().lower()
            match cmd:
                case "a":
                    self.start()
                case "b":
                    self.stop()
                case "c":
                    self.reset_possesso_palla()
                case "d":
                    self.set_tempo_aggiuntivo()
                case "e":
                    self.next_period()
                case "f":
                    self.goal_casa_piu()
                case "g":
                    self.goal_tasferta_piu()
                case "h":
                    self.sirena_on()
                case "i":
                    self.timeout_start()
                case "l":
                    self.timeout_reset()
                case "m":
                    self.timeout_start()
                case "p":
                    self.timeout_set_pausa_13()
                case "u":
                    self.update_display()
                case "w":
                    self.update_tabellone()
                case "q":
                    print("Uscita")
                    break
                case _:
                    print("❓ Comando sconosciuto, premi `?`")

    def _check_stato_sirena(self):
        if self.sirena and self._task_sirena is None:
            self._task_sirena = asyncio.create_task(self._sirena_off())

    async def _sirena_off(self):
        await asyncio.sleep(2)
        self.sirena = 0
        self._task_sirena = None

    def _min_sec_fmt(self, timing):
        if timing<1:
            minuti=0
            secondi=int(timing*100)
            return {"min": f"{minuti:02}", "sec": f"{secondi:02}"}
        minuti, secondi = divmod(int(math.ceil(timing)), 60)
        return {"min": f"{minuti:02}", "sec": f"{secondi:02}"}

    def _formato_tempo_possesso_palla(self):
        return int(math.ceil(self.tempo_possesso_palla))

    def update_display(self):  # da testare
        self.stop()
        self.publish("display/tempo", str(44))
        jts = json.dumps({"url": "http://10.42.0.1/display/main.py", "position": "main.py"})
        self.publish("display/update", jts)

    def update_tabellone(self):
        self.stop()
        jts = json.dumps({"url": "http://10.42.0.1/tabellone/main.py", "position": "main.py"})
        self.publish("tabellone/update", jts)