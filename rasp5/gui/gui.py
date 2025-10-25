""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 04/09/25

"""

import json
import paho.mqtt.client as mqtt
from PyQt6.QtWidgets import QMainWindow, QMessageBox
import tabellone
import asyncio

import game_controller

BROKER = "localhost"
TOPIC_STATO = "stato"


class Tabellone(QMainWindow, tabellone.Ui_TabelloneLED):
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

        self.buttonMinPlus.clicked.connect(self.add_min_plus)
        self.buttonMinMinus.clicked.connect(self.rem_min_plus)

        self.buttonSecPlus.clicked.connect(self.add_sec_plus)
        self.buttonSecMinus.clicked.connect(self.rem_sec_plus)

        self.buttonPeriodPlus.clicked.connect(self.incrementa_periodo)
        self.buttonPeriodMinus.clicked.connect(self.decrementa_period)

        self.buttonTimeoutHomePlus.clicked.connect(self.timeout_home_plus)
        self.buttonTimeoutHomeMinus.clicked.connect(self.timeout_home_minus)

        self.buttonTimeoutGuestPlus.clicked.connect(self.timeout_guest_plus)
        self.buttonTimeoutGuestMinus.clicked.connect(self.timeout_guest_minus)

        self.buttonStart.clicked.connect(self.start_game)
        self.buttonStop.clicked.connect(self.stop_game)
        self.buttonTimeReload.clicked.connect(self.safe_reload_time)
        self.buttonReset.clicked.connect(self.on_reset_clicked)
        self.buttonExit.clicked.connect(self.on_exit_clicked)
        self.buttonSirena.clicked.connect(self.sirena)

        self.buttonTimeoutCalled.clicked.connect(self.timeout_chiamato)
        self.buttonTimeout13.clicked.connect(self.timeout_13)
        self.buttonTimeoutHalf.clicked.connect(self.timeout_halftime)
        self.buttonTimeoutStart.clicked.connect(self.timeout_start)
        self.buttonTimeoutStop.clicked.connect(self.timeout_stop)
        self.buttonTimeoutReset.clicked.connect(self.timeout_reset)

        self.buttonPossessoPlus.clicked.connect(self.add_possesso_palla_plus)
        self.buttonPossessoMinus.clicked.connect(self.rem_possesso_palla_plus)


        self.mc_actionUnder12.triggered.connect(lambda:self._load_categoria("under12"))
        self.mc_actionragazzi.triggered.connect(lambda: self._load_categoria("ragazzi"))
        self.mc_actionallieve.triggered.connect(lambda: self._load_categoria("allieve"))
        self.mc_actionallievi.triggered.connect(lambda: self._load_categoria("allievi"))
        self.mc_actionjunioresF.triggered.connect(lambda: self._load_categoria("junioresF"))
        self.mc_actionPromozione.triggered.connect(lambda: self._load_categoria("promozione"))
        self.mc_actionMaster.triggered.connect(lambda: self._load_categoria("master"))
        self.showFullScreen()


    def goal_tolto_home(self):
        self.controller.goal_casa_meno()

    def goal_segnato_home(self):
        self.controller.goal_casa_piu()

    def add_min_plus(self):
        self.controller.aggiungi_minuto_gioco()

    def rem_min_plus(self):
        self.controller.togli_minuto_gioco()

    def add_sec_plus(self):
        self.controller.aggiungi_secondo_gioco()

    def rem_sec_plus(self):
        self.controller.togli_secondo_gioco()

    def add_possesso_palla_plus(self):
        self.controller.aggiungi_posesso_palla()

    def rem_possesso_palla_plus(self):
        self.controller.togli_posesso_palla()

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

    def on_reset_clicked(self):
        if self.controller.game_running:
            self.mostra_errore("Devi prima fermare il gicoo")
            return
        reply = QMessageBox.warning(
            None,
            "Conferma reset",
            "⚠️ Sei sicuro di voler resettare tutto?\n\nQuesta azione non può essere annullata.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            print("Eseguo reset totale...")
            self._reset_game()
        else:
            print("Reset annullato")

    def on_exit_clicked(self):
        if self.controller.game_running:
            self.mostra_errore("Devi prima fermare il gicoo")
            return
        reply = QMessageBox.warning(
            None,
            "Conferma uscita",
            "⚠️ Sei sicuro di voler uscire?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            try:
                asyncio.get_event_loop().stop()
            except:
                pass

    def safe_reload_time(self):
        if self.controller.game_running:
            self.mostra_errore("Devi prima fermare il gicoo")
            return
        reply = QMessageBox.warning(None,
            "Conferma Ricarica Tempo",
            "⚠️ Premendo Yes riporti il tempo di gioco al valore iniziale",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reload_time()
        else:
            print("Reset annullato")

    def mostra_errore(self,msg):
        QMessageBox.critical(self,
            "Azione non consentita",
            "⚠️ %s"%msg,
            QMessageBox.StandardButton.Ok
        )

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

    def reload_time(self):
        self.controller.reset_tempo_periodo()
        self.controller.reset_possesso_palla()

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

    def closeEvent(self, event):
        self.controller.shutdown()
        super().closeEvent(event)

    def _reset_game(self):
        self.controller.reset_match()

    def _load_categoria(self,value):
        self.controller.load_categoria(value)
        self.labelCategoriaText.setText(self.controller.label_categoria())

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