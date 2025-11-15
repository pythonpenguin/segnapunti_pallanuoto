# Avvio automatico

Copiare lo script **GuiPnCrema.service** presente nella directory tools in **~/.config/systemd/user/GuiPnCrema.service**
per lanciare il servizio in usermode.

Poi

```
systemctl --user daemon-reload
systemctl --user enable GuiPnCrema.service
systemctl --user start GuiPnCrema.service
```
