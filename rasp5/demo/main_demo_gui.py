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

async def input_loop(controller):
    while True:
        cmd = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        cmd = cmd.strip().lower()
        match cmd:
            case "a":
                controller.start()
            case "b":
                controller.stop()
            case "c":
                controller.reset_possesso_palla()
            case "d":
                controller.set_tempo_aggiuntivo()
            case "e":
                controller.next_period()
            case "f":
                controller.goal_casa_piu()
            case "g":
                controller.goal_tasferta_piu()
            case "h":
                controller.sirena_on()
            case "i":
                controller.timeout_start()
            case "l":
                controller.timeout_reset()
            case "m":
                controller.timeout_start()
            case "p":
                controller.timeout_set_pausa_13()
            case "u":
                controller.update_display()
            case "q":
                print("Uscita")
                break
            case _:
                print("❓ Comando sconosciuto, premi `?`")


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
    asyncio.ensure_future(input_loop(controller))

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
