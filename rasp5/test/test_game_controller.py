""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 11/08/25

"""

import unittest
import unittest.mock as mock
import asyncio

from rasp5.src.game_controller import GameController
from rasp5.src.game_configure import GameConfigure


class TestGameController(unittest.TestCase):

    def setUp(self):
        self.configuratore = GameConfigure("var/configurazione_serie.json")
        self.configuratore.read()
        mqtt_client_patch = mock.patch("paho.mqtt.client.Client")
        self.addCleanup(mqtt_client_patch.stop)
        self.mock_client_cls = mqtt_client_patch.start()
        self.mock_client = mock.MagicMock()
        self.mock_client_cls.return_value = self.mock_client

    def tearDown(self):
        pass

    def test_instance(self):
        self.assertIsInstance(GameController(self.configuratore), GameController)

    def test_connect(self):
        controller = GameController(self.configuratore)
        self.mock_client.connect.assert_not_called()
        self.mock_client.is_connected.return_value = False
        controller.connect_to_broker()
        self.mock_client.connect.assert_called_once_with("localhost", 300)

    def test_publish(self):
        controller = GameController(self.configuratore)
        self.mock_client.publish.assert_not_called()
        controller.publish("pippo", "pluto")
        self.mock_client.publish.assert_called_once_with("pippo", "pluto", retain=False)

    def test_tempo_periodo(self):
        controller = GameController(self.configuratore)
        self.assertEqual(480, controller.tempo_periodo)

    def test_start(self):
        controller = GameController(self.configuratore)
        self.assertEqual(480, controller.tempo_periodo)
        self.assertFalse(controller.game_running)
        controller.start()
        self.assertTrue(controller.game_running)

    def test_stop(self):
        controller = GameController(self.configuratore)
        self.assertEqual(480, controller.tempo_periodo)
        self.assertFalse(controller.game_running)
        controller.start()
        self.assertTrue(controller.game_running)
        controller.stop()
        self.assertFalse(controller.game_running)

    def test_gol_casa(self):
        controller = GameController(self.configuratore)
        self.assertEqual(0,controller.score_home)
        self.assertEqual(0, controller.score_away)
        controller.goal_home()
        self.assertEqual(1, controller.score_home)
        self.assertEqual(0, controller.score_away)

    def test_gol_trasferta(self):
        controller = GameController(self.configuratore)
        self.assertEqual(0,controller.score_home)
        self.assertEqual(0, controller.score_away)
        controller.goal_away()
        self.assertEqual(0, controller.score_home)
        self.assertEqual(1, controller.score_away)

    def test_gol_5_3(self):
        controller = GameController(self.configuratore)
        self.assertEqual(0,controller.score_home)
        self.assertEqual(0, controller.score_away)
        for _x in range(0,5):
            controller.goal_home()
        for _x in range(0,3):
            controller.goal_away()
        self.assertEqual(5, controller.score_home)
        self.assertEqual(3, controller.score_away)

    def test_sirena_on(self):
        controller = GameController(self.configuratore)
        self.assertEqual(0, controller.sirena)
        controller.sirena_on()
        self.assertEqual(1, controller.sirena)


class TestGameControllerLoop(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        super().setUp()
        self.configuratore = GameConfigure("var/configurazione_serie.json")
        self.configuratore.read()
        mqtt_client_patch = mock.patch("paho.mqtt.client.Client")
        self.addCleanup(mqtt_client_patch.stop)
        self.mock_client_cls = mqtt_client_patch.start()
        self.mock_client = mock.MagicMock()
        self.mock_client_cls.return_value = self.mock_client

    async def test_game_time_loop_mai_partito(self):
        controller = GameController(self.configuratore)
        self.assertEqual(480, controller.tempo_periodo)
        self.mock_client.assert_not_called()
        task = asyncio.create_task(controller.tempo_gioco_loop())
        await asyncio.sleep(1.5)
        task.cancel()
        self.mock_client.assert_not_called()

    async def test_game_time_loop_partito(self):
        controller = GameController(self.configuratore)
        self.assertEqual(480, controller.tempo_periodo)
        self.mock_client.publish.assert_not_called()
        controller.game_running = True
        task = asyncio.create_task(controller.tempo_gioco_loop())
        await asyncio.sleep(1.5)
        controller.game_running = False
        task.cancel()
        self.mock_client.publish.assert_not_called()
        self.assertLess(controller.tempo_periodo, 480)

    async def test_game_time_loop_start_stop(self):
        controller = GameController(self.configuratore)
        self.assertEqual(480, controller.tempo_periodo)
        self.mock_client.publish.assert_not_called()
        controller.game_running = True
        task = asyncio.create_task(controller.tempo_gioco_loop())
        await asyncio.sleep(0.1)
        controller.game_running = False
        self.assertLess(controller.tempo_periodo, 480)
        self.mock_client.publish.assert_not_called()
        controller.game_running = True
        await asyncio.sleep(1)
        task.cancel()
        self.assertLess(controller.tempo_periodo, 479)
        self.mock_client.publish.assert_not_called()

    async def test_refresh_prima_del_secondo(self):
        controller = GameController(self.configuratore)
        self.mock_client.publish.assert_not_called()
        task = asyncio.create_task(controller.refresh())
        await asyncio.sleep(0.1)
        task.cancel()
        self.mock_client.publish.assert_called_once_with('stato',
                                                         '{"tabellone": {"gol_casa": 0, "gol_trasferta": 0, "periodo": 1, "tempo_gioco": {"min": "08", "sec": "00"}}, "display": {"tempo": 28, "sirena": 0}}',
                                                         retain=False)

    async def test_refresh_dopo_un_secondo(self):
        controller = GameController(self.configuratore)
        self.mock_client.publish.assert_not_called()
        task = asyncio.create_task(controller.refresh())
        task_tgl = asyncio.create_task(controller.tempo_gioco_loop())
        controller.start()
        await asyncio.sleep(0.1)
        self.mock_client.publish.assert_called_once_with('stato',
                                                         '{"tabellone": {"gol_casa": 0, "gol_trasferta": 0, "periodo": 1, "tempo_gioco": {"min": "08", "sec": "00"}}, "display": {"tempo": 28, "sirena": 0}}',
                                                         retain=False)
        await asyncio.sleep(1.2)
        task.cancel()
        task_tgl.cancel()
        self.mock_client.publish.assert_any_call('stato',
                                                 '{"tabellone": {"gol_casa": 0, "gol_trasferta": 0, "periodo": 1, "tempo_gioco": {"min": "07", "sec": "59"}}, "display": {"tempo": 27, "sirena": 0}}',
                                                 retain=False)

    async def test_refresh_sirena_un_secondo(self):
        controller = GameController(self.configuratore)
        self.mock_client.publish.assert_not_called()
        task = asyncio.create_task(controller.refresh())
        task_tgl = asyncio.create_task(controller.tempo_gioco_loop())
