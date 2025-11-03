"""
:author: Davide Soresinetti
:email: davide.soresinetti@fitre.it
:date: 02/11/25
"""

import lgpio
import time

GPIOS = [4, 17, 14, 15, 18, 27, 22, 23, 24, 5, 6, 13]
DEBOUNCE_MICROS = 1000  # 1ms in microsecondi per debounce hardware
VALIDATION_READS = 5  # Numero di letture consecutive per validare
VALIDATION_DELAY = 0.002  # 2ms tra una lettura e l'altra

# Handle globale del chip
chip_handle = None


def validate_button_press(gpio, expected_level):
    """Valida la pressione del pulsante con letture multiple"""
    for _ in range(VALIDATION_READS):
        if lgpio.gpio_read(chip_handle, gpio) != expected_level:
            return False
        time.sleep(VALIDATION_DELAY)
    return True


def gpio_callback(chip, gpio, level, tick):
    """Callback per pulsanti in pull-down con validazione multipla"""
    # Valida con letture multiple usando il livello ricevuto dall'evento
    if validate_button_press(gpio, level):
        if level == 1:
            print(f"⚡ GPIO PREMUTO (VALIDATO) ---> {gpio}")
        else:
            print(f"🔄 GPIO RILASCIATO (VALIDATO) ---> {gpio}")
        print(f"⚡ VALUE ---> {level}")
        print(f"⚡ lgpio.gpio_read() ---> {lgpio.gpio_read(chip_handle, gpio)}")
    else:
        print(f"⚠ GPIO {gpio} - Evento spurio ignorato (level={level})")


def main():
    global chip_handle
    chip_handle = lgpio.gpiochip_open(0)
    h = chip_handle

    try:
        callbacks = []
        for gpio in GPIOS:
            edge_type = lgpio.BOTH_EDGES
            lgpio.gpio_claim_alert(h, gpio, edge_type, lgpio.SET_PULL_DOWN)

            # Imposta il debounce hardware
            lgpio.gpio_set_debounce_micros(h, gpio, DEBOUNCE_MICROS)

            # Registra la callback
            cb = lgpio.callback(h, gpio, edge_type, gpio_callback)
            callbacks.append(cb)

        print("✓ In attesa di eventi GPIO (CTRL+C per terminare)...")
        print(f"✓ Configurazione: PULL_DOWN + BOTH_EDGES")
        print(f"✓ Debounce hardware: {DEBOUNCE_MICROS / 1000}ms")
        print(f"✓ GPIO monitorati: {GPIOS}\n")

        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n✓ Programma terminato")
    finally:
        for cb in callbacks:
            cb.cancel()
        lgpio.gpiochip_close(h)


if __name__ == '__main__':
    main()
