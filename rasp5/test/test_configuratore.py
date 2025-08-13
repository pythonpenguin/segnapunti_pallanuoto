""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 11/08/25

"""

import unittest
import json
import os
import tempfile

from rasp5.src.game_configure import GameConfigure  # il tuo modulo

class TestGameConfigurePerCampo(unittest.TestCase):
    def setUp(self):
        # Crea cartella temporanea e file JSON con tutti i valori di test
        self.tmpdir = tempfile.TemporaryDirectory(dir="/tmp")
        self.test_file = os.path.join(self.tmpdir.name, "config_test.json")
        self.test_values = {
            "game_time": 720,
            "shot_time": 24,
            "periodi": 6,
            "shot_time_r": 14,
            "shot_time_enable": False,
            "timeout_time": 75,
            "time_end_period": 90,
            "half_time": 180
        }
        with open(self.test_file, "w") as f:
            json.dump(self.test_values, f)

        # Istanza già pronta con file valido
        self.cfg = GameConfigure(self.test_file)
        self.cfg.read()

        # Istanza già pronta con file mancante (default)
        self.cfg_default = GameConfigure("__fake__")
        self.cfg_default.read()

    def tearDown(self):
        self.tmpdir.cleanup()

    # ---- game_time -> tempo_periodo ----
    def test_default_game_time(self):
        self.assertEqual(self.cfg_default.tempo_periodo(), GameConfigure.DEFAULT["game_time"])

    def test_game_time(self):
        self.assertEqual(self.cfg.tempo_periodo(), self.test_values["game_time"])

    # ---- shot_time -> tempo_gioco ----
    def test_default_shot_time(self):
        self.assertEqual(self.cfg_default.tempo_gioco(), GameConfigure.DEFAULT["shot_time"])

    def test_shot_time(self):
        self.assertEqual(self.cfg.tempo_gioco(), self.test_values["shot_time"])

    # ---- periodi -> periodi_gioco ----
    def test_default_periodi(self):
        self.assertEqual(self.cfg_default.periodi_gioco(), GameConfigure.DEFAULT["periodi"])

    def test_periodi(self):
        self.assertEqual(self.cfg.periodi_gioco(), self.test_values["periodi"])

    # ---- shot_time_r -> tempo_aggiuntivo ----
    def test_default_shot_time_r(self):
        self.assertEqual(self.cfg_default.tempo_aggiuntivo(), GameConfigure.DEFAULT["shot_time_r"])

    def test_shot_time_r(self):
        self.assertEqual(self.cfg.tempo_aggiuntivo(), self.test_values["shot_time_r"])

    # ---- shot_time_enable -> tempo_effettivo ----
    def test_default_shot_time_enable(self):
        self.assertEqual(self.cfg_default.tempo_effettivo(), GameConfigure.DEFAULT["shot_time_enable"])

    def test_shot_time_enable(self):
        self.assertEqual(self.cfg.tempo_effettivo(), self.test_values["shot_time_enable"])

    # ---- timeout_time -> tempo_timeout ----
    def test_default_timeout_time(self):
        self.assertEqual(self.cfg_default.tempo_timeout(), GameConfigure.DEFAULT["timeout_time"])

    def test_timeout_time(self):
        self.assertEqual(self.cfg.tempo_timeout(), self.test_values["timeout_time"])

    # ---- time_end_period -> tempo_fine_periodo ----
    def test_default_time_end_period(self):
        self.assertEqual(self.cfg_default.tempo_fine_periodo(), GameConfigure.DEFAULT["time_end_period"])

    def test_time_end_period(self):
        self.assertEqual(self.cfg.tempo_fine_periodo(), self.test_values["time_end_period"])

    # ---- half_time -> tempo_meta_partita ----
    def test_default_half_time(self):
        self.assertEqual(self.cfg_default.tempo_meta_partita(), GameConfigure.DEFAULT["half_time"])

    def test_half_time(self):
        self.assertEqual(self.cfg.tempo_meta_partita(), self.test_values["half_time"])
