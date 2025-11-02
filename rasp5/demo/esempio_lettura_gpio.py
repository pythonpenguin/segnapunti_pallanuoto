""" 

:author: Davide Soresinetti
:email: davide.soresinetti@fitre.it
:date: 02/11/25

"""

""" 
:author: Davide Soresinetti
:email: davide.soresinetti@fitre.it
:date: 02/11/25
"""

import lgpio
import time

GPIOS = [4, 17, 14, 15, 18, 27, 22, 23, 24, 5, 6, 13]


def gpio_callback(chip, gpio, level, tick):
    """Chiamata quando viene rilevato un edge"""
    print(f"GPIO RILEVATO ---> {gpio}")


def main():
    h = lgpio.gpiochip_open(0)

    try:
        # Configura tutti i GPIO con callback
        for gpio in GPIOS:
            lgpio.gpio_claim_alert(h, gpio, lgpio.FALLING_EDGE, lgpio.SET_PULL_DOWN)
            # Imposta callback per questo GPIO
            cb = lgpio.callback(h, gpio, lgpio.FALLING_EDGE, gpio_callback)

        print("In attesa di eventi GPIO (CTRL+C per terminare)...")

        # Loop infinito - i callback gestiranno gli eventi
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgramma terminato")
    finally:
        lgpio.gpiochip_close(h)


if __name__ == '__main__':
    main()