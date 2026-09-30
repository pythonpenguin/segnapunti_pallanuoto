#!/usr/bin/env python3
"""
Verifica la qualità della connessione tra il Raspberry (hotspot) e gli ESP32.

Da eseguire sul Raspberry, come root (serve per iw e per il log di mosquitto):

    sudo python3 qualita_connessione.py [--intervallo 5] [--csv misure.csv]

Ogni intervallo stampa, per ogni dispositivo collegato all'hotspot:
segnale WiFi, bitrate, ping (perdite e latenza) e stato MQTT.
Gli eventi vengono segnalati appena accadono: disconnessioni WiFi,
riconnessioni e timeout MQTT, buchi nella pubblicazione dello stato.
Con CTRL+C (o `kill`, se lanciato in background) stampa un riepilogo.

Usa solo la libreria standard e i comandi iw, ping, ip, journalctl, tail, mosquitto_sub.
"""

import argparse
import csv
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict

IFACE = "wlan0"
IW = "/usr/sbin/iw"
MOSQUITTO_LOG = "/var/log/mosquitto/mosquitto.log"
TOPIC_STATO = ("display/stato", "tabellone/stato")
BUCO_STATO_S = 1.0  # il Raspberry pubblica lo stato ogni 250 ms: oltre 1 s è un buco
PING_PER_GIRO = 5

SEGNALE_BUONO = -67  # dBm
SEGNALE_SCARSO = -75

# MAC -> nome. Il MAC si ricava anche dal client_id MQTT (esp32 + MAC senza ":")
DISPOSITIVI = {
    "78:42:1c:8c:57:48": "display 28s #1",
    "ec:e3:34:ab:e7:d0": "tabellone",
    "ec:e3:34:ad:37:bc": "display 28s #2",
    "60:45:2e:4c:14:c7": "PC Davide",
}

RE_CONNESSO = re.compile(r"New client connected from ([\d.]+):\d+ as (\S+) \(.*k(\d+)\)")
RE_EVENTI_MQTT = (
    (re.compile(r"Client (\S+) has exceeded timeout"), False,
     "keepalive scaduto: il broker non riceveva più niente"),
    (re.compile(r"Client (\S+) closed its connection"), False, "ha chiuso la connessione"),
    (re.compile(r"Client (\S+) disconnected: (.*)"), False, "disconnesso"),
    (re.compile(r"Client (\S+) already connected, closing old connection"), None,
     "si è ricollegato sopra una sessione mezza aperta"),
    (re.compile(r"Outgoing messages are being dropped for client (\S+)"), None,
     "il broker scarta messaggi: il client non li riceve"),
)
RE_WIFI = re.compile(r"AP-STA-(CONNECTED|DISCONNECTED) ([0-9a-f:]{17})")

lock = threading.Lock()
mqtt = defaultdict(lambda: {"collegato": None, "k": None, "riconnessioni": 0, "problemi": 0})
wifi_disconnessioni = defaultdict(int)
stato_ultimo = {}
stato_buco_max = defaultdict(float)
stato_buchi = defaultdict(int)
stato_segnalato = set()
storico = defaultdict(lambda: {"segnale": [], "perdita": [], "rtt": []})
processi = []


def nome(mac):
    return DISPOSITIVI.get(mac, mac)


def mac_da_client_id(client_id):
    m = re.fullmatch(r"[a-z0-9]*([0-9a-f]{12})", client_id)  # esclude gli auto-XXXX dei client Python
    if not m:
        return None
    coda = m.group(1)
    return ":".join(coda[i:i + 2] for i in range(0, 12, 2))


def evento(messaggio):
    with lock:
        print(f"{time.strftime('%H:%M:%S')} ⚠ {messaggio}", flush=True)


def avvia(comando):
    # sessione separata: i figli ricevono solo i segnali che mandiamo noi alla chiusura
    proc = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                            start_new_session=True)
    processi.append(proc)
    return proc


def ferma_processi():
    # mosquitto_sub intercetta SIGTERM e ignora SIGPIPE: se non esce, va ucciso
    for proc in processi:
        proc.terminate()
    for proc in processi:
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def interrompi(_segnale, _frame):
    raise KeyboardInterrupt


def in_background(funzione, *args):
    threading.Thread(target=funzione, args=args, daemon=True).start()


# --- MQTT: log di mosquitto ---------------------------------------------------

def interpreta_log(riga, dal_vivo=True):
    m = RE_CONNESSO.search(riga)
    if m:
        ip, client_id, k = m.groups()
        mac = mac_da_client_id(client_id)
        if mac is None:
            return
        with lock:
            mqtt[mac].update(collegato=True, k=int(k))
            if dal_vivo:
                mqtt[mac]["riconnessioni"] += 1
        if dal_vivo:
            vecchio = ", codice VECCHIO" if k == "0" else ""
            evento(f"MQTT {nome(mac)} collegato da {ip} (keepalive {k} s{vecchio})")
        return
    for regex, collegato, descrizione in RE_EVENTI_MQTT:
        m = regex.search(riga)
        if not m:
            continue
        mac = mac_da_client_id(m.group(1))
        if mac is None:
            return
        with lock:
            if collegato is not None:
                mqtt[mac]["collegato"] = collegato
            if dal_vivo:
                mqtt[mac]["problemi"] += 1
        if dal_vivo:
            dettaglio = f": {m.group(2)}" if regex.groups > 1 else ""
            evento(f"MQTT {nome(mac)} {descrizione}{dettaglio}")
        return


def segui_log_mosquitto():
    precedente = subprocess.run(["tail", "-n", "5000", MOSQUITTO_LOG], capture_output=True, text=True)
    for riga in precedente.stdout.splitlines():
        interpreta_log(riga, dal_vivo=False)
    for riga in avvia(["tail", "-n0", "-F", MOSQUITTO_LOG]).stdout:
        interpreta_log(riga)


# --- WiFi: eventi dell'hotspot ------------------------------------------------

def segui_wifi():
    for riga in avvia(["journalctl", "-f", "-n0", "-o", "cat", "-t", "wpa_supplicant"]).stdout:
        m = RE_WIFI.search(riga)
        if not m:
            continue
        tipo, mac = m.groups()
        if tipo == "DISCONNECTED":
            with lock:
                wifi_disconnessioni[mac] += 1
            evento(f"WiFi {nome(mac)} scollegato dall'hotspot")
        else:
            evento(f"WiFi {nome(mac)} collegato all'hotspot")


# --- Stato pubblicato dal Raspberry -------------------------------------------

def segui_stato():
    comando = ["mosquitto_sub", "-h", "localhost", "-v"]
    for topic in TOPIC_STATO:
        comando += ["-t", topic]
    for riga in avvia(comando).stdout:
        topic = riga.split(" ", 1)[0]
        adesso = time.monotonic()
        with lock:
            prima = stato_ultimo.get(topic)
            stato_ultimo[topic] = adesso
            stato_segnalato.discard(topic)
            if prima is None:
                continue
            buco = adesso - prima
            stato_buco_max[topic] = max(stato_buco_max[topic], buco)
            if buco > BUCO_STATO_S:
                stato_buchi[topic] += 1
        if buco > BUCO_STATO_S:
            evento(f"{topic}: nessuna pubblicazione per {buco:.1f} s")


def controlla_stato_fermo():
    adesso = time.monotonic()
    for topic in TOPIC_STATO:
        with lock:
            ultimo = stato_ultimo.get(topic)
            if ultimo is None or topic in stato_segnalato or adesso - ultimo < 5:
                continue
            stato_segnalato.add(topic)
        evento(f"{topic}: il Raspberry non pubblica da {adesso - ultimo:.0f} s")


# --- Misure periodiche ----------------------------------------------------------

def leggi_stazioni():
    uscita = subprocess.run([IW, "dev", IFACE, "station", "dump"], capture_output=True, text=True).stdout
    stazioni = {}
    corrente = None
    for riga in uscita.splitlines():
        m = re.match(r"Station ([0-9a-f:]{17})", riga)
        if m:
            corrente = stazioni[m.group(1)] = {}
        elif corrente is not None and ":" in riga:
            chiave, valore = riga.strip().split(":", 1)
            numero = re.match(r"\s*(-?\d+(?:\.\d+)?)", valore)
            if numero:
                corrente[chiave] = float(numero.group(1))
    return stazioni


def leggi_ip():
    uscita = subprocess.run(["ip", "neigh", "show", "dev", IFACE], capture_output=True, text=True).stdout
    indirizzi = {}
    for riga in uscita.splitlines():
        parti = riga.split()
        if "lladdr" in parti:
            indirizzi[parti[parti.index("lladdr") + 1]] = parti[0]
    return indirizzi


def ping(ip, risultati):
    uscita = subprocess.run(["ping", "-q", "-n", "-c", str(PING_PER_GIRO), "-i", "0.2", "-W", "1", ip],
                            capture_output=True, text=True).stdout
    perdita = re.search(r"(\d+(?:\.\d+)?)% packet loss", uscita)
    rtt = re.search(r"= [\d.]+/([\d.]+)/([\d.]+)/", uscita)
    risultati[ip] = (float(perdita.group(1)) if perdita else 100.0,
                     float(rtt.group(1)) if rtt else None,
                     float(rtt.group(2)) if rtt else None)


def giudizio(mac, segnale, perdita):
    problemi = []
    if segnale is not None and segnale < SEGNALE_SCARSO:
        problemi.append("segnale debole")
    elif segnale is not None and segnale < SEGNALE_BUONO:
        problemi.append("segnale al limite")
    if perdita:
        problemi.append("ping persi")
    if mac in mqtt and mqtt[mac]["collegato"] is False:
        problemi.append("MQTT giù")
    elif mac in mqtt and mqtt[mac]["k"] == 0:
        problemi.append("codice vecchio")
    return ", ".join(problemi) or "ok"


def testo_mqtt(mac):
    if mac not in mqtt:
        return "-"
    stato = mqtt[mac]
    if stato["collegato"] is None:
        return "?"
    return f"{'ok' if stato['collegato'] else 'GIÙ'} k{stato['k']}"


def fmt(valore, formato="{:.0f}"):
    return "-" if valore is None else formato.format(valore)


def giro(scrittore_csv):
    stazioni = leggi_stazioni()
    indirizzi = leggi_ip()
    risultati = {}
    thread = [threading.Thread(target=ping, args=(indirizzi[mac], risultati))
              for mac in stazioni if mac in indirizzi]
    for t in thread:
        t.start()
    for t in thread:
        t.join()
    controlla_stato_fermo()

    righe = []
    for mac, s in sorted(stazioni.items(), key=lambda x: nome(x[0])):
        ip = indirizzi.get(mac, "-")
        perdita, rtt_medio, rtt_max = risultati.get(ip, (None, None, None))
        segnale = s.get("signal avg", s.get("signal")) or None  # iw a volte riporta 0 al primo giro
        with lock:
            if segnale is not None:
                storico[mac]["segnale"].append(segnale)
            if perdita is not None:
                storico[mac]["perdita"].append(perdita)
            if rtt_max is not None:
                storico[mac]["rtt"].append(rtt_max)
            mq = testo_mqtt(mac)
            esito = giudizio(mac, segnale, perdita)
        righe.append((nome(mac), ip, fmt(s.get("signal")), fmt(segnale), fmt(s.get("tx bitrate")),
                      fmt(perdita, "{:.0f}%"), f"{fmt(rtt_medio)}/{fmt(rtt_max)}",
                      fmt(s.get("inactive time")), fmt(s.get("connected time")), mq, esito))
        if scrittore_csv:
            scrittore_csv.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), nome(mac), mac, ip, s.get("signal"),
                                    segnale, s.get("tx bitrate"), perdita, rtt_medio, rtt_max,
                                    s.get("inactive time"), s.get("connected time"), mq, esito])

    assenti = [nome(mac) for mac in DISPOSITIVI if mac not in stazioni]
    with lock:
        buchi = "  ".join(f"{t.split('/')[0]} max {stato_buco_max.pop(t, 0):.2f}s" for t in TOPIC_STATO)
        print(f"\n{time.strftime('%H:%M:%S')}  {'dispositivo':<18} {'IP':<13} {'dBm':>4} {'media':>5} "
              f"{'Mbit':>5} {'persi':>5} {'rtt ms':>9} {'inatt.':>6} {'conn.s':>6}  {'MQTT':<7} esito")
        for r in righe:
            print(f"          {r[0]:<18} {r[1]:<13} {r[2]:>4} {r[3]:>5} {r[4]:>5} {r[5]:>5} {r[6]:>9} "
                  f"{r[7]:>6} {r[8]:>6}  {r[9]:<7} {r[10]}")
        if assenti:
            print(f"          non collegati al WiFi: {', '.join(assenti)}")
        print(f"          stato pubblicato: {buchi}", flush=True)


def riepilogo(inizio):
    durata = time.monotonic() - inizio
    print(f"\n===== Riepilogo ({durata / 60:.1f} min) =====")
    macs = set(storico) | {m for m in mqtt if m in DISPOSITIVI} | set(wifi_disconnessioni)
    for mac in sorted(macs, key=nome):
        h = storico[mac]
        segnale = (f"segnale min/medio/max {min(h['segnale']):.0f}/"
                   f"{sum(h['segnale']) / len(h['segnale']):.0f}/{max(h['segnale']):.0f} dBm"
                   if h["segnale"] else "mai visto sul WiFi")
        parti = [segnale]
        if h["perdita"]:
            parti.append(f"ping persi {sum(h['perdita']) / len(h['perdita']):.1f}%")
        if h["rtt"]:
            ordinati = sorted(h["rtt"])
            p95 = ordinati[min(len(ordinati) - 1, int(len(ordinati) * 0.95))]
            parti.append(f"rtt max {ordinati[-1]:.0f} ms (95% sotto {p95:.0f})")
        eventi = f"WiFi persi {wifi_disconnessioni[mac]}"
        if mac in mqtt:
            eventi += f", MQTT riconnessioni {mqtt[mac]['riconnessioni']}, problemi {mqtt[mac]['problemi']}"
        parti.append(eventi)
        print(f"  {nome(mac):<18} " + "; ".join(parti))
    for topic in TOPIC_STATO:
        print(f"  {topic}: buchi oltre {BUCO_STATO_S:.0f} s: {stato_buchi[topic]}")


def main():
    parser = argparse.ArgumentParser(description="Qualità della connessione Raspberry <-> ESP32")
    parser.add_argument("--intervallo", type=float, default=5, help="secondi tra una misura e l'altra")
    parser.add_argument("--csv", help="salva le misure anche in questo file CSV")
    args = parser.parse_args()
    if os.geteuid() != 0:
        sys.exit("Serve root: sudo python3 " + sys.argv[0])

    file_csv = open(args.csv, "a", newline="") if args.csv else None
    scrittore = csv.writer(file_csv) if file_csv else None
    if file_csv and file_csv.tell() == 0:
        scrittore.writerow(["ora", "dispositivo", "mac", "ip", "segnale", "segnale_medio", "bitrate",
                            "ping_persi", "rtt_medio", "rtt_max", "inattivo_ms", "connesso_s", "mqtt", "esito"])

    signal.signal(signal.SIGTERM, interrompi)
    signal.signal(signal.SIGINT, interrompi)  # anche se lanciato in background con &
    for funzione in (segui_log_mosquitto, segui_wifi, segui_stato):
        in_background(funzione)
    print(f"Controllo connessione su {IFACE} ogni {args.intervallo:.0f} s. CTRL+C per il riepilogo.")
    inizio = time.monotonic()
    try:
        while True:
            partenza = time.monotonic()
            giro(scrittore)
            if file_csv:
                file_csv.flush()
            time.sleep(max(0.0, args.intervallo - (time.monotonic() - partenza)))
    except KeyboardInterrupt:
        pass
    finally:
        ferma_processi()
        riepilogo(inizio)
        if file_csv:
            file_csv.close()


if __name__ == "__main__":
    main()
