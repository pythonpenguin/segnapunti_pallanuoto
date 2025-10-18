""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 08/08/25

"""
import json


class GameConfigure(object):
    SERIE = "configurazione_serie.json"

    DEFAULT = {"game_time": 30, "shot_time": 28, "periodi": 4, "shot_time_r": 18,
               "shot_time_enable": True,"timeout_time": 60,"time_end_period":60,"half_time":120,
               "max_timeouts":2,"label_categoria":"Carica Categoria"}

    def __init__(self, ppathname=SERIE):
        self.file_cfg = ppathname
        self.cfg = {}
        self._categoria_scelta="__fake__"
        self._current_cfg=self.DEFAULT.copy()

    def read(self):
        try:
            with open(self.file_cfg) as json_file:
                self.cfg = json.load(json_file)
        except FileNotFoundError:
            print("File {} non trovato".format(self.file_cfg))

    def tempo_gioco(self):
        return self._get("shot_time")

    def periodi_gioco(self):
        return self._get("periodi")

    def tempo_periodo(self):
        return self._get("game_time")

    def tempo_aggiuntivo(self):
        return self._get("shot_time_r")

    def tempo_effettivo(self):
        return self._get("shot_time_enable")

    def tempo_timeout(self):
        return self._get("timeout_time")

    def tempo_fine_periodo(self):
        return self._get("time_end_period")

    def tempo_meta_partita(self):
        return self._get("half_time")

    def numero_timeouts(self):
        return self._get("max_timeouts")

    def set_categoria(self, categoria):
        self._categoria_scelta = categoria
        self._current_cfg = self.cfg.get(self._categoria_scelta,self.DEFAULT.copy())

    def get_label_categoria(self):
        return self._get("label_categoria")

    def _get(self,field):
        return self._current_cfg.get(field)