"""
:author: Davide Soresinetti
:email: davide.soresinetti@fitre.it
:date: 02/11/25
"""

import lgpio
import time

GPIOS = [4, 17, 14, 15, 18, 27, 22, 23, 24, 5, 6, 13]
DEBOUNCE_TIME = 0.010  # 10 millisecondi
VERIFY_DELAY = 0.002  # 2ms per verifica stato stabile

# Handle globale del chip
chip_handle = None
last_event_time = {gpio: 0 for gpio in GPIOS}


def gpio_callback(chip, gpio, level, tick):
    """Callback con debounce e verifica stato stabile"""
    global last_event_time, chip_handle

    current_time = time.time()

    # Debounce: ignora se troppo vicino all'ultimo evento
    if current_time - last_event_time[gpio] < DEBOUNCE_TIME:
        return

    # Attendi un attimo per stabilizzazione
    time.sleep(VERIFY_DELAY)

    # Verifica che lo stato sia ancora basso (pressione vera)
    if lgpio.gpio_read(chip_handle, gpio) == 0:
        print(f"GPIO RILEVATO ---> {gpio}")
        last_event_time[gpio] = current_time


def main():
    global chip_handle
    chip_handle = lgpio.gpiochip_open(0)
    h = chip_handle

    try:
        callbacks = []
        for gpio in GPIOS:
            lgpio.gpio_claim_alert(h, gpio, lgpio.FALLING_EDGE, lgpio.SET_PULL_DOWN)
            cb = lgpio.callback(h, gpio, lgpio.FALLING_EDGE, gpio_callback)
            callbacks.append(cb)

        print("In attesa di eventi GPIO (CTRL+C per terminare)...")
        print(f"Debounce: {DEBOUNCE_TIME * 1000}ms, Verifica: {VERIFY_DELAY * 1000}ms")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgramma terminato")
    finally:
        for cb in callbacks:
            cb.cancel()
        lgpio.gpiochip_close(h)


if __name__ == '__main__':
    main()