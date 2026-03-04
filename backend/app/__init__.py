from flask import Flask 
from .config import Config

from .functions import DB 
from .mqtt import MQTT  

app = Flask(__name__)
app.config.from_object(Config) 

# Create MongoDB instance to get access to all the functions defined in functions.py
mongo = DB(Config)
Mqtt  = MQTT(mongo)
try:
    Mqtt.client.loop_start()
    print("MQTT: loop_start initialized")
except Exception as e:
    print(f"MQTT: loop_start failed: {e}")

from app import views
