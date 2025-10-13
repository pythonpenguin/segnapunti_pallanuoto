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

### Piccola diagnostica

```sudo iwconfig 
[sudo] password di davide: 
lo        no wireless extensions.

wlp0s20f3  IEEE 802.11  ESSID:"PallanuotoCrema"  
          Mode:Managed  Frequency:2.412 GHz  Access Point: 14:5D:34:BF:3D:87   
          Bit Rate=72.2 Mb/s   Tx-Power=22 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Encryption key:off
          Power Management:on
          Link Quality=48/70  Signal level=-62 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:33   Missed beacon:0
```

`sudo iw dev wlan0 scan | egrep "SSID|signal:|primary channel"` esegue lo scan delle reti

## Controllo temperatura ventola

Usa il comando `vcgencmd measure_temp`
