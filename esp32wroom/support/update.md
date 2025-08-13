# Procedura di update

import urequests;url="http://10.42.0.1/main.py";nome_file = "main.py";response = urequests.get(url)
with open(nome_file, "w") as f:
    f.write(response.text)
import machine
machine.reset()