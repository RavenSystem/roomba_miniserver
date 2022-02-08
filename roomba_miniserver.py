#!/usr/bin/env python3
# Roomba Mini Server
# (C) 2022 Jose Antoinio Jimenez Campos

# Requirements:
# python3 -m pip install paho-mqtt

####### USER CONFIG
roomba_host = '';
roomba_port = 8883;
roomba_blid = '';
roomba_pass = '';
roomba_pmap = '';

roomba_jobs = {
    'bedroom': [ 9, 11],
    'bath': [ 3 ],
}

miniserver_port = 8765;
roomba_prefix = 'roomba_';
#######

import sys
import socket;
import ssl;
import time;
import paho.mqtt.client as mqtt;

def on_message_callback(client, userdata, message):
    print("* RECEIVED = ", str(message.payload.decode("utf-8")));
    print("* TOPIC = ", message.topic);
    print("* QOS = ", message.qos);
    print("* RETAIN FLAGS = ", message.retain);
    print("");

client = mqtt.Client(client_id = roomba_blid, clean_session = True, protocol = mqtt.MQTTv311);

context = ssl.SSLContext();
context.set_ciphers('HIGH:!DH:!aNULL');
#context.set_ciphers('DEFAULT@SECLEVEL=1');
client.tls_set_context(context);
client.tls_insecure_set(True);
client.username_pw_set(roomba_blid, roomba_pass);

if (len(sys.argv) > 1 and str(sys.argv[1]) == 'info'):
    try:
        client.connect(roomba_host, port = roomba_port);
    except:
        exit(-1);
        
    client.on_message = on_message_callback;
    client.loop_start();
    client.subscribe('#');
    time.sleep(3);
    client.loop_stop();
    client.disconnect();
    exit(0);


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
miniserver_host = socket.gethostname();
s.bind((miniserver_host, miniserver_port));
s.listen(10);

while True:
    conn, addr = s.accept();
    data = conn.recv(64);
    conn.close();
    message = data.decode('ascii').rstrip();
    #print(message);
    
    if (message.startswith(roomba_prefix)):
        roomba_message = message.replace(roomba_prefix, '');
        
        jobs = roomba_jobs.get(roomba_message, '');
        
        try:
            client.connect(roomba_host, port = roomba_port);
            client.publish('cmd', '{"command": "stop", "time": 0, "initiator": "localApp"}');
            time.sleep(3);
        except:
            continue;
            
        if (jobs != ''):
            jobs_json_array = '';
            
            for job in jobs:
                jobs_json_array += '{"region_id":"' + str(job) + '","type":"rid"},'
            
            client.publish('cmd', '{"command":"start","regions":[' + jobs_json_array[:-1] + '],"ordered":1,"pmap_id": "' + roomba_pmap + '","time":0,"initiator":"localApp"}');
        
        else:
            client.publish('cmd', '{"command": "' + roomba_message + '", "time": 0, "initiator": "localApp"}');

        client.disconnect();
