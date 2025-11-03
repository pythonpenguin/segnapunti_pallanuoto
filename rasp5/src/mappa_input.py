"""

:author: Davide Soresinetti
:email: davide.soresinetti@fitre.it
:date: 03/11/25

Modulo per mappare gli input GPIO ai metodi del GameController
usando lgpio e asyncio.
"""

import lgpio
import asyncio
import time
from typing import Callable, Optional


class MappaInput:
    """Gestisce la mappatura tra GPIO e azioni del game controller"""

    # Configurazione GPIO
    GPIOS = [4, 17, 14, 15, 18, 27, 22, 23, 24, 5, 6, 13]
    DEBOUNCE_MICROS = 1000  # 1ms debounce hardware
    VALIDATION_READS = 5  # Numero di letture per validare
    VALIDATION_DELAY = 0.002  # 2ms tra letture

    # Mappatura GPIO -> Azione secondo mappa_bottoni.md
    GPIO_MAPPING = {
        23: ("goal_casa_piu", "RISING_EDGE"),           # Bottone 1
        17: ("goal_casa_meno", "RISING_EDGE"),          # Bottone 2
        24: (None, "RISING_EDGE"),                       # Bottone 3 - non mappato
        6: (None, "RISING_EDGE"),                        # Bottone 4 - non mappato
        13: ("start_stop", "BOTH_EDGES"),                # Bottone 5 - start/stop
        5: (None, "RISING_EDGE"),                        # Bottone 6 - non mappato
        18: ("goal_tasferta_piu", "RISING_EDGE"),       # Bottone 7
        27: ("goal_tasferta_meno", "RISING_EDGE"),      # Bottone 8
        15: (None, "RISING_EDGE"),                       # Bottone 9 - non mappato
        22: (None, "RISING_EDGE"),                       # Bottone 10 - non mappato
        14: (None, "RISING_EDGE"),                       # Bottone 11 - non mappato
        4: (None, "RISING_EDGE"),                        # Bottone 12 - non mappato
    }

    def __init__(self, game_controller):
        """
        Inizializza il mapper degli input GPIO.

        :param game_controller.GameController game_controller: Il controller di gioco
        """
        self.game_controller = game_controller
        self.chip_handle = None
        self.callbacks = []
        self._loop_enable = True
        self._event_queue = None  # Creata quando l'event loop è disponibile
        self._event_loop = None

    def validate_button_press(self, gpio: int, expected_level: int) -> bool:
        """
        Valida la pressione del pulsante con letture multiple.

        :param gpio: Numero GPIO
        :param expected_level: Livello atteso (0 o 1)
        :return: True se validato, False altrimenti
        """
        for _ in range(self.VALIDATION_READS):
            if lgpio.gpio_read(self.chip_handle, gpio) != expected_level:
                return False
            time.sleep(self.VALIDATION_DELAY)
        return True

    def _gpio_callback(self, chip, gpio, level, tick):
        """
        Callback asincrona per eventi GPIO.
        Thread-safe: mette l'evento in una queue per processing asincrono.

        :param chip: Chip handle
        :param gpio: Numero GPIO
        :param level: Livello del segnale (0 o 1)
        :param tick: Timestamp
        """
        # Ignora se event loop non è ancora pronto
        if self._event_queue is None or self._event_loop is None:
            return

        # Valida l'evento
        if not self.validate_button_press(gpio, level):
            # Silenzioso per GPIO non mappati, altrimenti avvisa
            action, _ = self.GPIO_MAPPING.get(gpio, (None, None))
            if action is not None:
                print(f"⚠ GPIO {gpio} - Evento spurio ignorato (level={level})")
            return

        # Metti l'evento validato nella queue per processing asincrono
        try:
            self._event_loop.call_soon_threadsafe(
                self._event_queue.put_nowait, (gpio, level)
            )
        except Exception as e:
            print(f"⚠ Errore nella callback GPIO {gpio}: {e}")

    async def _process_events(self):
        """
        Processa gli eventi GPIO dalla queue in modo asincrono.
        """
        while self._loop_enable:
            try:
                gpio, level = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1
                )
                await self._handle_gpio_event(gpio, level)
            except asyncio.TimeoutError:
                continue

    async def _handle_gpio_event(self, gpio: int, level: int):
        """
        Gestisce un evento GPIO validato, chiamando il metodo appropriato
        del GameController.

        :param gpio: Numero GPIO
        :param level: Livello del segnale
        """
        action, edge_type = self.GPIO_MAPPING.get(gpio, (None, None))

        if action is None:
            print(f"ℹ GPIO {gpio} - Non mappato")
            return

        # Gestione speciale per start/stop (GPIO 13)
        if action == "start_stop":
            if level == 1:
                print(f"▶ START (GPIO {gpio})")
                self.game_controller.start()
            else:
                print(f"⏸ STOP (GPIO {gpio})")
                self.game_controller.stop()
        else:
            # Azioni normali: esegui solo su RISING_EDGE (level=1)
            if level == 1:
                method = getattr(self.game_controller, action, None)
                if method and callable(method):
                    print(f"⚡ Azione: {action} (GPIO {gpio})")
                    method()
                else:
                    print(f"⚠ Metodo {action} non trovato nel GameController")

    def setup_gpio(self):
        """
        Configura i GPIO e registra le callback.
        """
        self.chip_handle = lgpio.gpiochip_open(0)

        for gpio in self.GPIOS:
            action, edge_type = self.GPIO_MAPPING.get(gpio, (None, "RISING_EDGE"))

            # Determina il tipo di edge
            if edge_type == "BOTH_EDGES":
                edge = lgpio.BOTH_EDGES
            else:
                edge = lgpio.RISING_EDGE

            # Configura GPIO con pull-down
            lgpio.gpio_claim_alert(self.chip_handle, gpio, edge, lgpio.SET_PULL_DOWN)

            # Imposta debounce hardware
            lgpio.gpio_set_debounce_micros(self.chip_handle, gpio, self.DEBOUNCE_MICROS)

            # Registra callback
            cb = lgpio.callback(self.chip_handle, gpio, edge, self._gpio_callback)
            self.callbacks.append(cb)

            status = "MAPPATO" if action else "NON MAPPATO"
            print(f"✓ GPIO {gpio:2d} configurato - {edge_type:12s} - {status:12s} - {action or ''}")

    async def start(self):
        """
        Avvia il processing degli eventi GPIO.
        Deve essere chiamato all'interno di un event loop asyncio.
        """
        # Inizializza event loop e queue
        self._event_loop = asyncio.get_event_loop()
        self._event_queue = asyncio.Queue()

        # Setup GPIO dopo aver preparato la queue
        self.setup_gpio()
        print("\n✓ MappaInput attivo - In attesa di eventi GPIO...")
        await self._process_events()

    def shutdown(self):
        """
        Chiude le risorse GPIO in modo pulito.
        """
        self._loop_enable = False

        # Cancella le callback
        for cb in self.callbacks:
            cb.cancel()

        # Chiudi il chip
        if self.chip_handle is not None:
            lgpio.gpiochip_close(self.chip_handle)

        print("\n✓ MappaInput terminato")


async def main():
    """
    Esempio di utilizzo del MappaInput con GameController.
    Include sia input GPIO che input da tastiera.
    """
    from game_configure import GameConfigure
    from game_controller import GameController

    # Setup
    config = GameConfigure()
    controller = GameController(config)
    mapper = MappaInput(controller)

    # Connetti al broker MQTT
    controller.connect_to_broker()

    try:
        # Avvia i task: GPIO + tastiera + controller loops
        await asyncio.gather(
            controller.refresh(),
            controller.tempo_gioco_loop(),
            controller.input_loop(),  # Input da tastiera
            mapper.start()             # Input da GPIO
        )
    except KeyboardInterrupt:
        print("\n⏹ Interruzione ricevuta")
    finally:
        mapper.shutdown()
        controller.shutdown()


if __name__ == "__main__":
    asyncio.run(main())