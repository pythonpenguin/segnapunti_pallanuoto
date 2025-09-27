""" 

..author: Davide Soresinetti
..email: davide.soresinetti@fitre.it
..date: 04/09/25

"""

import tkinter as tk
import paho.mqtt.client as mqtt


class ScoreboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tabellone Pallanuoto")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)

        # Labels
        self.time_var = tk.StringVar(value="08:00")
        self.periodo_var = tk.StringVar(value="1")
        self.home_var = tk.StringVar(value="0")
        self.guest_var = tk.StringVar(value="0")
        self.shot_var = tk.StringVar(value="30")

        tk.Label(root, textvariable=self.home_var,
                 font=("Arial", 100, "bold"), fg="red", bg="black").pack(side="left", expand=True)
        tk.Label(root, textvariable=self.time_var,
                 font=("Arial", 80), fg="white", bg="black").pack(side="left", expand=True)
        tk.Label(root, textvariable=self.guest_var,
                 font=("Arial", 100, "bold"), fg="green", bg="black").pack(side="left", expand=True)

        tk.Label(root, text="Periodo", font=("Arial", 30), fg="yellow", bg="black").pack()
        tk.Label(root, textvariable=self.periodo_var,
                 font=("Arial", 40), fg="yellow", bg="black").pack()

        tk.Label(root, text="Shot", font=("Arial", 30), fg="orange", bg="black").pack()
        tk.Label(root, textvariable=self.shot_var,
                 font=("Arial", 40), fg="orange", bg="black").pack()

    def update_value(self, key, value):
        if key == "display/tempo":
            self.time_var.set(value)
        elif key == "gioco/periodo":
            self.periodo_var.set(value)
        elif key == "gioco/casa":
            self.home_var.set(value)
        elif key == "gioco/ospiti":
            self.guest_var.set(value)
        elif key == "gioco/shot":
            self.shot_var.set(value)

# MQTT callback
def on_message(client, userdata, msg):
    topic = msg.topic
    value = msg.payload.decode()
    app.update_value(topic, value)

BROKER = "0.0.0.0"

root = tk.Tk()
app = ScoreboardApp(root)

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER)
client.subscribe("display/#")
client.subscribe("gioco/#")
client.loop_start()

root.mainloop()
