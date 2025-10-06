""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 06/10/25

"""

import sys, asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from game_controller import GameController
import game_configure
from gui import Tabellone

async def main_async(controller):
    # avvia i loop principali del controller
    await asyncio.gather(
        controller.tempo_gioco_loop(),
        controller.refresh()
    )

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # inizializza controller e GUI
    # NB: qui puoi passare il tuo game_configurator reale
    game_config = game_configure.GameConfigure()
    controller = GameController(game_config)
    controller.connect_to_broker()

    gui = Tabellone(controller)
    gui.show()

    # avvia i loop asyncio del controller
    asyncio.ensure_future(main_async(controller))

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
