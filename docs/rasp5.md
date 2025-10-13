# Configurazioni di rete

- attivare hotspost con indirizzo 10.42.0.1
- nmcli dev wifi hotspot ifname wlan0 ssid PallanuotoCrema password latuapwd band bg con-name PallanuotoCrema
  - band bg è obbligatorio per avere solo wpa3
  - nmcli connection modify "PallanuotoCrema" connection.autoconnect yes per renderla permanente.

## Comandi utili

`nmcli connection show PallanuotoCrema` permette di vedere i dettagli della connessione
`sudo iw dev wlan0 station dump` per vedere i dettagli degli oggetti collegati
`sudo arp -a` mostra i mac address degli oggetti connessi

## Parametri opzionali per antenna esterna

`sudo nmcli connection modify PallanuotoCrema 802-11-wireless.powersave 2`

per verificare

```nmcli connection show PallanuotoCrema | egrep "mode|band|channel|powersave"
802-11-wireless.mode:                   ap
802-11-wireless.band:                   bg
802-11-wireless.channel:                1
802-11-wireless.powersave:              2 (disable)
ipv6.addr-gen-mode:                     default
```

Scrivere un file come il seguente

```cat /etc/modprobe.d/rtw88.conf
options rtw88_core disable_ps=1
options rtw88_core disable_lps_deep=1
options rtw88_core disable_aspm=1
```

### disabilitare il wifi interno

Aprire il file **/boot/firmware/config.txt** e aggiungere

```[all]
dtoverlay=disable-wifi
```
