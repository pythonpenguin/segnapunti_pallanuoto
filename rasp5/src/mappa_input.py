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
import logging
from typing import Callable, Optional

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mappa_input.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MappaInput')


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
        24: ("next_period", "RISING_EDGE"),                       # Bottone 3 - non mappato
        6: ("reset_possesso_palla", "RISING_EDGE"),      # Bottone 4 - 28 secondi
        13: ("start_stop", "BOTH_EDGES"),                # Bottone 5 - start/stop
        5: ("set_tempo_aggiuntivo", "RISING_EDGE"),      # Bottone 6 - 18 secondi
        18: ("goal_tasferta_piu", "RISING_EDGE"),       # Bottone 7
        27: ("goal_tasferta_meno", "RISING_EDGE"),      # Bottone 8
        15: ("prev_period", "RISING_EDGE"),                       # Bottone 9 - non mappato
        22: (None, "RISING_EDGE"),                       # Bottone 10 - non mappato
        14: (None, "RISING_EDGE"),                       # Bottone 11 - non mappato
        4: ("sirena_on_off", "BOTH_EDGES"),                        # Bottone 12 - non mappato
    }

    def __init__(self, game_controller):
        """
        Inizializza il mapper degli input GPIO.

        :param game_controller.GameController game_controller: Il controller di gioco
        """
        logger.info("Inizializzazione MappaInput")
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
                logger.debug(f"GPIO {gpio} - Validazione fallita, lettura inconsistente")
                return False
            time.sleep(self.VALIDATION_DELAY)
        logger.debug(f"GPIO {gpio} - Validazione OK (level={expected_level})")
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
            logger.warning(f"GPIO {gpio} - Event loop non ancora pronto, evento ignorato")
            return

        # Valida l'evento
        if not self.validate_button_press(gpio, level):
            # Silenzioso per GPIO non mappati, altrimenti avvisa
            action, _ = self.GPIO_MAPPING.get(gpio, (None, None))
            if action is not None:
                logger.warning(f"GPIO {gpio} - Evento spurio ignorato (level={level})")
            return

        # Metti l'evento validato nella queue per processing asincrono
        try:
            self._event_loop.call_soon_threadsafe(
                self._event_queue.put_nowait, (gpio, level)
            )
            logger.debug(f"GPIO {gpio} - Evento accodato (level={level})")
        except Exception as e:
            logger.error(f"Errore nella callback GPIO {gpio}: {e}", exc_info=True)

    async def _process_events(self):
        """
        Processa gli eventi GPIO dalla queue in modo asincrono.
        """
        logger.info("Avvio loop _process_events() - processing eventi GPIO dalla queue")
        while self._loop_enable:
            try:
                gpio, level = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1
                )
                logger.debug(f"Processing evento GPIO {gpio}, level={level}")
                await self._handle_gpio_event(gpio, level)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Errore nel processing eventi GPIO: {e}", exc_info=True)

    async def _handle_gpio_event(self, gpio: int, level: int):
        """
        Gestisce un evento GPIO validato, chiamando il metodo appropriato
        del GameController.

        :param gpio: Numero GPIO
        :param level: Livello del segnale
        """
        action, edge_type = self.GPIO_MAPPING.get(gpio, (None, None))

        if action is None:
            logger.info(f"GPIO {gpio} - Non mappato")
            return

        # Gestione speciale per start/stop (GPIO 13)
        if action == "start_stop":
            if level == 1:
                logger.info(f"START richiesto (GPIO {gpio})")
                self.game_controller.start()
            else:
                logger.info(f"STOP richiesto (GPIO {gpio})")
                self.game_controller.stop()
            return
        if action == "sirena_on_off":
            match level:
                case 0:
                    self.game_controller.sirena_off()
                    logger.info(f"SIRENA OFF (GPIO {gpio})")
                case 1:
                    self.game_controller.sirena_on()
                    logger.info(f"SIRENA ON (GPIO {gpio})")
                case _:
                    logger.warning(f"INVALID VALUE per sirena (GPIO {gpio}, level={level})")
            return
        # Azioni normali: esegui solo su RISING_EDGE (level=1)
        if level == 1:
            method = getattr(self.game_controller, action, None)
            if method and callable(method):
                logger.info(f"Azione: {action} (GPIO {gpio})")
                method()
            else:
                logger.error(f"Metodo {action} non trovato nel GameController")

    def setup_gpio(self):
        """
        Configura i GPIO e registra le callback.
        """
        logger.info("Setup GPIO - apertura chip")
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
            logger.info(f"GPIO {gpio:2d} configurato - {edge_type:12s} - {status:12s} - {action or ''}")

    async def start(self):
        """
        Avvia il processing degli eventi GPIO.
        Deve essere chiamato all'interno di un event loop asyncio.
        """
        logger.info("Avvio MappaInput")
        # Inizializza event loop e queue
        self._event_loop = asyncio.get_event_loop()
        self._event_queue = asyncio.Queue()

        # Setup GPIO dopo aver preparato la queue
        self.setup_gpio()
        logger.info("MappaInput attivo - In attesa di eventi GPIO")
        await self._process_events()

    def shutdown(self):
        """
        Chiude le risorse GPIO in modo pulito.
        """
        logger.info("Shutdown MappaInput")
        self._loop_enable = False

        # Cancella le callback
        for cb in self.callbacks:
            cb.cancel()

        # Chiudi il chip
        if self.chip_handle is not None:
            lgpio.gpiochip_close(self.chip_handle)

        logger.info("MappaInput terminato")


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