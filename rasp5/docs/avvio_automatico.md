# Avvio automatico

Creare lo script `/etc/systemd/system/GuiPnCrema.service` con

```
[Unit]
Description=Pallanuoto GUI
After=graphical-session.target network-online.target
Wants=graphical-session.target network-online.target

[Service]
Type=simple
ExecStart=/home/davide/python_venv/bin/python /home/davide/segnapunti_pallanuoto/rasp5/gui/giuria_gui.py
WorkingDirectory=/home/davide/segnapunti_pallanuoto/
Restart=on-failure
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority
StandardOutput=append:%h/giuria_gui.log
StandardError=append:%h/giuria_gui.log

[Install]
WantedBy=graphical-session.target
```

poi

```
sudo systemctl daemon-reload
sudo systemctl enable GuiPnCrema.service
sudo systemctl start GuiPnCrema.service
```

verifica che linger sia attivo `loginctl show-user davide | grep Linger`


`sudo loginctl enable-linger davide`