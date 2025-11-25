# Istruzioni per Gui in QT

## Disegno interfaccia

Per disegnerare l'interfaccia ho usato un file .ui che la descrive. Per trasformare da questo fil ad un *.py che 
contiene tutti i comandi ho usato il pyuic6: `pyuic6 -x rasp5/gui/tabellone.ui -o rasp5/gui/tabellone.py`

Adesso basta importare tabellone.py per avere tutti i comandi necessari