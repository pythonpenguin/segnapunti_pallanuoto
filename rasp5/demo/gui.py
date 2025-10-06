""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 04/09/25

"""

import sys, json
import paho.mqtt.client as mqtt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QGridLayout
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt
from PyQt6 import uic

import game_controller

BROKER = "localhost"
TOPIC_STATO = "stato"

class Tabellone(QWidget):
    def __init__(self, controller: game_controller.GameController):
        super().__init__()
        self.controller = controller
        uic.loadUi("tabellone.ui", self)

        # MQTT client per ricevere aggiornamenti
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(BROKER)
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
        self.buttonReset.clicked.connect(self.reset_game)
        self.buttonSirena.clicked.connect(self.sirena)

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

        except Exception as e:
            print("Errore parsing stato:", e)

    def _refresh_tempo_gioco(self,msg):
        """

        :param dict msg:
        :return:
        """
        if isinstance(msg, dict):
            self.labelMainTime.setText(f"{msg['min']}:{msg['sec']}")
        else:
            self.labelMainTime.setText("--:--")

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