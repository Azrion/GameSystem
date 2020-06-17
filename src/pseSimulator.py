"""
Simulates a PSE system
"""

# Imports
import time
import paho.mqtt.client as mqtt

# IP address and port
mqttIP = "localhost"
mqttPort = 1883


# PSE simulator
def PSE(pse_client):
    """
    :param pse_client: MQTT client
    """
    pse_client.connect(mqttIP, mqttPort, 60)
    moods = ["good", "bad"]
    engagements = ["high", "low"]
    idx = 0

    while True:
        idx += 2
        if (idx % 2) == 0:
            idx = 1
        else:
            idx = 0

        mood = moods[idx]
        engagement = engagements[idx]

        pse_output_msg = mood + ',' + engagement
        print("[PSE] Publishing output to 'pse_output' topic: ", pse_output_msg)
        pse_client.publish("topic/pse_output", pse_output_msg)

        time.sleep(1)


# Main function
if __name__ == '__main__':
    PSE(mqtt.Client())
