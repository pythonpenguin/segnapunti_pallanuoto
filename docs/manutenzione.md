# Ambiente virtuale python

## Installazione da zero

Per creare l'ambiente virtuale in cui installare tutti i pacchetti necessari usare
`python3 -m venv directory_di_destinazione`, esempio `python3 -m venv pncremaenv`

Python creerà la directory pncremaenv e ci installa una copia virtuale di se stesso.

A questo punto andare nella directory pncremaenv da shell e scrivere `source bin/activate` quindi
`pip install -r requirements.txt` dive **requirements.txt**  è il file di questo progetto che contiene tutti i pacchetti
necessari.

# Aggiornamento pacchetti installati 

Conviene installare pip-review per tener aggiornati i pacchetti  

```bash
pip install pip-review
pip-review --auto
```
