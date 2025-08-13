""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 08/08/25

"""
import json


class GameConfigure(object):
    SERIE = "configurazione_serie.json"

    ALLIEVE = "allieve"
    JUNIORES_F = "juniores_f"
    JUNIORES_M = "juniores_m"
    RAGAZZI = "ragazzi"
    ALLIEVI = "allievi"
    ESORDIENTI = "esordienti"
    MASTER = "master"
    PROMOZIONE = "promozione"

    DEFAULT = {"game_time": 480, "shot_time": 28, "periodi": 4, "shot_time_r": 18,
               "shot_time_enable": True,"timeout_time": 60,"time_end_period":60,"half_time":120}

    def __init__(self, ppathname=SERIE):
        self.file_cfg = ppathname
        self.cfg = {}

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

    def _get(self,field):
        return self.cfg.get(field,self.DEFAULT[field])