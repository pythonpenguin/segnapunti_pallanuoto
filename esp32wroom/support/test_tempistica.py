""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 03/08/25

"""


import paho.mqtt.publish as publish
import time

def main():
    while True:
        for _x in range(15,-1,-1):
            if _x == 14:
                publish.single(topic="display/sirena", payload=str(0), qos=1, retain=True, hostname="localhost")
            publish.single(topic="display/tempo",payload=str(_x),qos=1,retain=True,hostname="localhost")
            time.sleep(0.3)
        else:
            publish.single(topic="display/sirena", payload=str(1), qos=1, retain=True, hostname="localhost")

if __name__ == '__main__':
    main()