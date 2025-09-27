# Configurazioni di rete

- attivare hotspost con indirizzo 10.42.0.1
- nmcli dev wifi hotspot ifname wlan0 ssid PallanuotoCrema password latuapwd band bg con-name PallanuotoCrema
  - band bg è obbligatorio per avere solo wpa3
  - nmcli connection modify "PallanuotoCrema" connection.autoconnect yes per renderla permanente.
