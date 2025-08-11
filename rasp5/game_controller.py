""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 08/08/25

"""
import asyncio
from paho.mqtt import client as mqtt


class GameController(object):
    def __init__(self,game_configurator, mqtt_host="localhost",keepalive=300):
        """

        :param game_configure.GameConfigure game_configurator:
        :param mqtt_host:
        :param keepalive:
        """
        self.game_config = game_configurator
        self.client = mqtt.Client()
        self.client.connect(mqtt_host,keepalive=keepalive)

        self.tempo_periodo = self.game_config.tempo_periodo()
        self.tempo_gioco = self.game_config.tempo_gioco()
        self.tempo_timeout = self.game_config.tempo_timeout()
        self.tempo_pausa_periodi_1_3 = self.game_config.tempo_fine_periodo()
        self.tempo_pause_meta_partita = self.game_config.tempo_meta_partita()

        self.period = 1
        self.max_periodi = self.game_config.periodi_gioco()
        self.score_home = 0
        self.score_away = 0

        self.game_running = False
        self.shot_running = False
        self.timeout_running = False

        self._game_time_last_update = asyncio.get_event_loop().time()

    def publish(self, topic, msg,retain=False):
        print(f"[MQTT] {topic} => {msg}")
        self.client.publish(topic, msg,retain=retain)

    def publish_all(self):
        self.publish("game/time", self.format_game_time(self.tempo_periodo))
        self.publish("display/tempo", str(self.tempo_gioco))
        self.publish("game/score", f"{self.score_home:02d} {self.score_away:02d}")
        self.publish("game/period", str(self.period))
        if self.timeout_running:
            self.publish("game/timeout", self.to_mmss(self.tempo_timeout))
        else:
            self.publish("game/timeout", "OFF")

    def format_game_time(self, t):
        if t > 1.0:
            return f"{int(t) // 60:02d}:{int(t) % 60:02d}"
        else:
            return f"{t:04.1f}"

    def to_mmss(self, sec):
        return f"{sec // 60:02d}:{sec % 60:02d}"

    def start(self):
        self.game_running = True
        self.shot_running = True
        self._game_time_last_update = asyncio.get_event_loop().time()
        self._publish_shot_time()

    def stop(self):
        print("⏸ STOP")
        if self.timeout_running:
            return
        self.game_running = False
        self.shot_running = False

    def _publish_shot_time(self):
        self.publish("display/tempo", str(self.tempo_gioco))

    def reset_tempo_gioco(self):
        self.tempo_gioco = self.game_config.tempo_gioco()

    def set_tempo_aggiuntivo(self):
        if self.tempo_gioco < self.game_config.tempo_aggiuntivo():
            self.tempo_gioco = self.game_config.get_tempo_aggiuntivo()
            self._publish_shot_time()

    def next_period(self):
        if self.period <= self.max_periodi:
            self.period += 1
            self.tempo_periodo = self.game_config.tempo_periodo()
            self.publish("game/period", str(self.period))
            self.publish("game/time", self.format_game_time(self.tempo_periodo))
            self.sirena()

    def goal_home(self):
        self.score_home += 1
        print(f"Gol CASA → {self.score_home}")
        self.publish("game/score", f"{self.score_home:02d} {self.score_away:02d}")

    def goal_away(self):
        self.score_away += 1
        print(f"Gol TRASFERTA → {self.score_away}")
        self.publish("game/score", f"{self.score_home:02d} {self.score_away:02d}")

    def sirena(self):
        print("SIRENA")
        self.publish("game/sirena", "ON")
        asyncio.create_task(self._sirena_off())

    async def _sirena_off(self):
        await asyncio.sleep(2)
        self.publish("game/sirena", "OFF")

    def start_timeout(self):
        self.stop()
        self.timeout_running = True
        self.publish("game/timeout", self.to_mmss(self.tempo_timeout))

    async def game_time_loop(self):
        while True:
            now = asyncio.get_event_loop().time()
            if self.game_running and self.tempo_periodo > 0:
                if self.tempo_periodo > 1.0:
                    if now - self._game_time_last_update >= 1.0:
                        self.tempo_periodo -= 1.0
                        self._game_time_last_update = now
                        self.publish("game/time", self.format_game_time(self.tempo_periodo))
                else:
                    if now - self._game_time_last_update >= 0.1:
                        self.tempo_periodo -= 0.1
                        self._game_time_last_update = now
                        if self.tempo_periodo <= 0:
                            self.tempo_periodo = 0
                            self.game_running = False
                            print("⏱ Fine tempo")
                            self.sirena()
                        self.publish("game/time", self.format_game_time(self.tempo_periodo))
            await asyncio.sleep(0.01)

    async def second_based_loop(self):
        while True:
            if self.shot_running and self.tempo_gioco >= 0:
                self.tempo_gioco -= 1
                self._publish_shot_time()
                if self.tempo_gioco <= 0:
                    self.shot_running = False
                    self.game_running = False
                    self.sirena()
                    self.reset_tempo_gioco()
                    self._publish_shot_time()
            if self.timeout_running and self.tempo_timeout > 0:
                self.tempo_timeout -= 1
                self.publish("game/timeout", self.to_mmss(self.tempo_timeout))
                if self.tempo_timeout == 0:
                    print("⏱ Fine timeout")
                    self.timeout_running = False
                    self.publish("game/timeout", "OFF")
                    self.sirena()

            await asyncio.sleep(1)
