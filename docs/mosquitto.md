# Installazione

sudo apt install mosquitto

## Configurazione senza tls

- file in /etc/mosquitto/mosquitto.conf
  - listener porta indirizzo: listener 1883 0.0.0.0
  - allow_anonymous true
  - persistence false perchè non abbiamo necessità di salvare nulla

## configurazione demone

`sudo systemctl edit mosquitto.service` per aprire il file di configurazione aggiuntiva del demone

> [Service]
> 
> ExecStartPre=/bin/sleep 15

In questo modo il servizio parte dopo la rete. 

## Comandi utili

- cat /var/log/mosquitto/mosquitto.log