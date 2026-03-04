########################################################################################################
#                                                                                                      #
#   MQTT Paho Documentation - https://eclipse.dev/paho/index.php?page=clients/python/docs/index.php    #
#                                                                                                      #
########################################################################################################
import paho.mqtt.client as mqtt
from random import randint
from json import dumps, loads
from time import sleep
# from .config import Config
# from .functions import DB 

class MQTT:

    STUDENT_ID = "620169874"
    ID = f"IOT_B_{STUDENT_ID}"

    #  DEFINE ALL TOPICS TO SUBSCRIBE TO
    sub_topics = [(f"{STUDENT_ID}_pub", 0), (STUDENT_ID, 0), (f"{STUDENT_ID}_sub", 0)] #  A list of tuples of (topic, qos). Both topic and qos must be present in the tuple.
    host = "www.yanacreations.com"
    port = 1883
    keepalive = 60


    def __init__(self,mongo):
       
        self.randint                = randint
        self.loads                  = loads
        self.dumps                  = dumps
        self.sleep                  = sleep
        self.mongo                  = mongo
        self.client                 = mqtt.Client(client_id= self.ID, clean_session=True, reconnect_on_failure = True)
        self.client.on_connect      = self.on_connect
        self.client.on_message      = self.on_message
        self.client.on_disconnect   = self.on_disconnect
        self.client.on_subscribe    = self.on_subscribe


        # REGISTER CALLBACK FUNCTION FOR EACH TOPIC
        self.client.message_callback_add(self.STUDENT_ID, self.update)
        self.client.message_callback_add(f"{self.STUDENT_ID}_pub", self.toggle)

        # ADD MQTT SERVER AND PORT INFORMATION BELOW
        try:
            self.client.connect(self.host, self.port, self.keepalive)
        except Exception as e:
            print(f"MQTT: Initial connect failed: {str(e)}")
       


    def connack_string(self,rc):
        connection = {0: "Connection successful", 1: "Connection refused - incorrect protocol version", 2: "Connection refused - invalid client identifier", 3: "Connection refused - server unavailable", 4: "Connection refused - bad username or password", 5: "Connection refused - not authorised" }
        return connection[rc]

 
    def on_connect(self,client, userdata, flags, rc):
        # Called when the broker responds to our connection request.
        print("\n\nMQTT: "+ self.connack_string(rc)," ID: ",client._client_id.decode('utf-8'))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.sub_topics)     
 
    def on_subscribe(self, client, userdata, mid, granted_qos):   
        # Called when the broker responds to a subscribe request.   
        print("MQTT: Subscribed to", [topic[0] for topic in self.sub_topics])

    def publish(self,topic,payload):
        try:
            if not self.client.is_connected():
                try:
                    self.client.reconnect()
                    self.sleep(0.2)
                except Exception as reconnect_error:
                    print(f"MQTT: Reconnect before publish failed: {str(reconnect_error)}")
                    try:
                        self.client.connect(self.host, self.port, self.keepalive)
                        self.sleep(0.2)
                    except Exception as connect_error:
                        print(f"MQTT: Connect before publish failed: {str(connect_error)}")
                        return False
            info = self.client.publish(topic, payload)
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"MQTT: Publish rc error {info.rc}")
                return False
            info.wait_for_publish(timeout=2.0)
            return True
        
        except Exception as e:
            print(f"MQTT: Publish failed {str(e)}")
            return False


    def on_message(self,client, userdata, msg):
        # The callback for when a PUBLISH message is received from the server.
        try:
            print(msg.topic+" "+str(msg.payload.decode("utf-8")))
        except Exception as e:
            print(f"MQTT: onMessage Error: {str(e)}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("MQTT: Unexpected Disconnection.")
   

    # DEFINE CALLBACK FUNCTIONS FOR EACH TOPIC
    def update(self, client, userdata, msg):
        try:
            topic   = msg.topic
            payload = msg.payload.decode("utf-8")
            # print(payload) # UNCOMMENT WHEN DEBUGGING  
            
            update  = loads(payload) # CONVERT FROM JSON STRING TO JSON OBJECT  
            print(update) 

        except Exception as e:
            print(f"MQTT: GDP Error: {str(e)}")

    def toggle(self,client, userdata, msg):    
        '''Process messages from Frontend'''
        try:
            topic   = msg.topic
            payload = msg.payload.decode("utf-8")
            # print(payload) # UNCOMMENT WHEN DEBUGGING
            update  = loads(payload) # CONVERT FROM JSON STRING TO JSON OBJECT              
            print(update)

        except Exception as e:
            print(f"MQTT: toggle Error - {str(e)}")



     

