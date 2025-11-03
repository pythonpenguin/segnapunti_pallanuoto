"""
:author: Davide Soresinetti
:email: davide.soresinetti@fitre.it
:date: 02/11/25
"""

import lgpio
import time

GPIOS = [4, 17, 14, 15, 18, 27, 22, 23, 24, 5, 6, 13]
DEBOUNCE_TIME = 0.05  # 50ms (aumentato per eliminare rimbalzi)

# Handle globale del chip
chip_handle = None
last_event_time = {gpio: 0 for gpio in GPIOS}


def gpio_callback(chip, gpio, level, tick):
    """Callback con debounce per pulsanti in pull-down"""
    global last_event_time

    current_time = time.time()

    # Debounce: ignora se troppo vicino all'ultimo evento
    if current_time - last_event_time[gpio] < DEBOUNCE_TIME:
        return

    # Evento valido
    print(f"⚡ GPIO PREMUTO ---> {gpio}")
    last_event_time[gpio] = current_time


def main():
    global chip_handle
    chip_handle = lgpio.gpiochip_open(0)
    h = chip_handle

    try:
        callbacks = []
        for gpio in GPIOS:
            # Configura input con pull-down
            lgpio.gpio_claim_input(h, gpio, lgpio.SET_PULL_DOWN)

            # Rileva RISING_EDGE (0→1) quando si preme il pulsante!
            lgpio.gpio_claim_alert(h, gpio, lgpio.RISING_EDGE)
            cb = lgpio.callback(h, gpio, lgpio.RISING_EDGE, gpio_callback)
            callbacks.append(cb)

        print("✓ In attesa di eventi GPIO (CTRL+C per terminare)...")
        print(f"✓ Configurazione: PULL_DOWN + RISING_EDGE")
        print(f"✓ Debounce: {DEBOUNCE_TIME * 1000}ms")
        print(f"✓ GPIO monitorati: {GPIOS}\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n✓ Programma terminato")
    finally:
        for cb in callbacks:
            cb.cancel()
        lgpio.gpiochip_close(h)


if __name__ == '__main__':
    main()