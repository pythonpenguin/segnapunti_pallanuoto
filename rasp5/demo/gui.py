""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 04/09/25

"""

import json
import paho.mqtt.client as mqtt
from PyQt6.QtWidgets import QMainWindow,QWidget
import tabellone

import game_controller

BROKER = "localhost"
TOPIC_STATO = "stato"

class Tabellone(QWidget,tabellone.Ui_TabelloneLED):
    def __init__(self, controller: game_controller.GameController,broker=BROKER):
        super().__init__()
        self.setupUi(self)
        self.controller = controller

        # MQTT client per ricevere aggiornamenti
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(broker,keepalive=5)
        self.client.subscribe(TOPIC_STATO)
        self.client.loop_start()

        self.buttonHomePlus.clicked.connect(self.goal_segnato_home)
        self.buttonHomeMinus.clicked.connect(self.goal_tolto_home)

        self.buttonGuestPlus.clicked.connect(self.goal_segnato_trasferta)
        self.buttonGuestMinus.clicked.connect(self.goal_tolto_trasferta)

        self.buttonPeriodPlus.clicked.connect(self.incrementa_periodo)
        self.buttonPeriodMinus.clicked.connect(self.decrementa_period)

        self.buttonTimeoutHomePlus.clicked.connect(self.timeout_home_plus)
        self.buttonTimeoutHomeMinus.clicked.connect(self.timeout_home_minus)

        self.buttonTimeoutGuestPlus.clicked.connect(self.timeout_guest_plus)
        self.buttonTimeoutGuestMinus.clicked.connect(self.timeout_guest_minus)

        self.buttonStart.clicked.connect(self.start_game)
        self.buttonStop.clicked.connect(self.stop_game)
        self.buttonTimeReload.clicked.connect(self.timeout_reload_time)
        self.buttonReset.clicked.connect(self.reset_game)
        self.buttonSirena.clicked.connect(self.sirena)

        self.buttonTimeoutCalled.clicked.connect(self.timeout_chiamato)
        self.buttonTimeout13.clicked.connect(self.timeout_13)
        self.buttonTimeoutHalf.clicked.connect(self.timeout_halftime)
        self.buttonTimeoutStart.clicked.connect(self.timeout_start)
        self.buttonTimeoutStop.clicked.connect(self.timeout_stop)
        self.buttonTimeoutReset.clicked.connect(self.timeout_reset)

    def goal_segnato_home(self):
        self.controller.goal_casa_piu()

    def goal_tolto_home(self):
        self.controller.goal_casa_meno()

    def goal_segnato_trasferta(self):
        self.controller.goal_tasferta_piu()

    def goal_tolto_trasferta(self):
        self.controller.goal_tasferta_meno()

    def incrementa_periodo(self):
        self.controller.next_period()

    def decrementa_period(self):
        self.controller.prev_period()

    def timeout_home_plus(self):
        self.controller.timeout_casa_piu()

    def timeout_home_minus(self):
        self.controller.timeout_casa_meno()

    def timeout_guest_plus(self):
        self.controller.timeout_trasferta_piu()

    def timeout_guest_minus(self):
        self.controller.timeout_trasferta_meno()

    def start_game(self):
        self.controller.start()

    def stop_game(self):
        self.controller.stop()

    def reset_game(self):
        self.controller.reset_match()

    def sirena(self):
        self.controller.sirena_on()

    def timeout_chiamato(self):
        self.controller.timeout_set_chiamato_squadre()

    def timeout_13(self):
        self.controller.timeout_set_pausa_13()

    def timeout_halftime(self):
        self.controller.timeout_set_half_time()

    def timeout_start(self):
        self.controller.timeout_start()

    def timeout_stop(self):
        self.controller.timeout_stop()

    def timeout_reload_time(self):
        self.controller.reset_tempo_periodo()

    def timeout_reset(self):
        self.controller.timeout_reset()

    def on_message(self, client, userdata, msg):
        try:
            stato = json.loads(msg.payload.decode())
            tab = stato["tabellone"]
            self._refresh_tempo_gioco(tab["tempo_gioco"])
            self._refresh_gol_casa(tab["gol_casa"])
            self._refresh_gol_trasferta(tab["gol_trasferta"])
            self._refresh_periodo(tab["periodo"])
            self._refresh_timeout_casa(tab["timeout_casa"])
            self._refresh_timeout_trasferta(tab["timeout_trasferta"])
            self._refresh_timeout_clock(tab["timeout_clock"])
            self._refresh_possesso_palla(stato["display"]["tempo"])
        except Exception as e:
            print("Errore parsing stato:", e)

    def _refresh_possesso_palla(self,msg):
        self.labelPossesso.setText(str(msg))

    def _refresh_tempo_gioco(self,msg):
        self._refresh_clock(msg,self.labelMainTime)

    def _refresh_clock(self,msg,label):
        """

        :param dict msg:
        :return:
        """
        if isinstance(msg, dict):
            label.setText(f"{msg['min']}:{msg['sec']}")
        else:
            label.setText("--:--")

    def _refresh_gol_casa(self,value):
        self.labelHomeScore.setText(str(value))

    def _refresh_gol_trasferta(self,value):
        self.labelGuestScore.setText(str(value))

    def _refresh_periodo(self,value):
        self.labelPeriod.setText(str(value))

    def _refresh_timeout_casa(self,value):
        self.labelTimeOutHome.setText(str(value))

    def _refresh_timeout_trasferta(self,value):
        self.labelTimeOutGuest.setText(str(value))

    def _refresh_timeout_clock(self,msg):
        self._refresh_clock(msg, self.labelTimeoutClock)