""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 06/08/25

"""

import asyncio
import sys

from rasp5.src.game_controller import GameController
from rasp5.src.game_configure import GameConfigure

async def main():
    configurer = GameConfigure()
    controller = GameController(configurer)

    async def input_loop():
        while True:
            cmd = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            cmd = cmd.strip().lower()
            match cmd:
                case "s": controller.start()
                case "x": controller.stop()
                case "3": controller.reset_possesso_palla()
                case "2": controller.set_tempo_aggiuntivo()
                case "p": controller.next_period()
                case "h": controller.goal_home()
                case "a": controller.goal_away()
                case "z": controller.sirena_on()
                case "t": controller.start_timeout()
                case "u": controller.update_display()
                case "q":
                    print("Uscita")
                    break
                case _: print("❓ Comando sconosciuto, premi `?`")

    await asyncio.gather(input_loop(),controller.tempo_gioco_loop(),)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrotto")
