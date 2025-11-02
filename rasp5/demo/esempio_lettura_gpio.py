""" 

:author: Davide Soresinetti
:email: davide.soresinetti@fitre.it
:date: 02/11/25

"""

import gpiod
from gpiod.line import Direction,Bias,Edge

GPIOS = [4.17,14,15,18,27,22,23,24,5,6,13]

def main():
    chip = gpiod.Chip('gpiochip0')
    cfg = {x:gpiod.LineSettings(direction=Direction.INPUT,edge_detection=Edge.FALLING,debounce_period_us=10000,
                                bias=Bias.PULL_DOWN) for x in GPIOS}
    request = chip.request_lines(cfg,"console")
    try:
        while True:
            if request.wait_edge_events(timeout=1.0):
                events = request.read_edge_events()
                for event in events:
                    print(f"GPIO RILEVATO ---> {event.line_offset}")
    except KeyboardInterrupt:
        print("\nProgramma terminato")

if __name__ == '__main__':
    main()