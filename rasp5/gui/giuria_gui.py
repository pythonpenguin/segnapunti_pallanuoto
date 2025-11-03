""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 06/10/25

"""
import os
import sys
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
THIS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__)))
print(THIS_DIR)

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from game_controller import GameController
import game_configure
from gui import Tabellone
from mappa_input import MappaInput


# BROKER = "10.42.0.1"
BROKER = "localhost"

async def main_async(controller, mapper):
    # avvia i loop principali del controller + input GPIO
    await asyncio.gather(
        controller.tempo_gioco_loop(),
        controller.refresh(),
        controller.input_loop(),  # Input da tastiera
        mapper.start()             # Input da GPIO
    )


def main():
    app = QApplication(sys.argv)
    QApplication.setStyle("fusion")
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # inizializza controller e GUI
    var_dir = os.path.normpath(os.path.join(THIS_DIR,"..","var"))
    file_cfg_path = os.path.join(var_dir,"configurazione_serie.json")
    print(file_cfg_path)
    game_config = game_configure.GameConfigure(file_cfg_path)
    game_config.read()
    controller = GameController(game_config, BROKER)
    controller.connect_to_broker()

    # inizializza il mapper GPIO
    mapper = MappaInput(controller)

    gui = Tabellone(controller, BROKER)
    gui.show()

    # avvia i loop asyncio del controller + GPIO mapper
    asyncio.ensure_future(main_async(controller, mapper))

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
