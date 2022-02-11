#!/usr/bin/env python3
# Roomba Mini Server
# (C) 2022 Jose Antonio Jimenez Campos

# Requirements:
# python3 -m pip install paho-mqtt

####### USER CONFIG
roomba_host = '';
roomba_port = 8883;
roomba_blid = '';
roomba_pass = '';
roomba_pmap = '';

roomba_jobs = {
    'bedroom': [ 9, 11 ],
    'bath': [ 3 ],
}

miniserver_port = 8765;
roomba_prefix = 'roomba_';
#######

import sys
import socket;
import ssl;
import datetime;
import time;
import paho.mqtt.client as mqtt;

def on_message_callback(client, userdata, message):
    print("* RECEIVED = ", str(message.payload.decode("utf-8")));
    print("* TOPIC = ", message.topic);
    print("* QOS = ", message.qos);
    print("* RETAIN FLAGS = ", message.retain);
    print("");

print("Roomba MiniServer (c) 2022 Jose A. Jimenez Campos");

client = mqtt.Client(client_id = roomba_blid, clean_session = True, protocol = mqtt.MQTTv311);

context = ssl.SSLContext(protocol = ssl.PROTOCOL_TLS_CLIENT);
context.check_hostname = False;
context.verify_mode = ssl.CERT_NONE;
context.set_ciphers('HIGH:!DH:!aNULL');
#context.set_ciphers('DEFAULT@SECLEVEL=1');
client.tls_set_context(context);
client.tls_insecure_set(True);
client.username_pw_set(roomba_blid, roomba_pass);

if (len(sys.argv) > 1 and str(sys.argv[1]) == 'info'):
    print("Retrieving INFO");
    try:
        client.connect(roomba_host, port = roomba_port);
    except:
        print("! Connect to Roomba");
        exit(-1);
        
    client.on_message = on_message_callback;
    client.loop_start();
    client.subscribe('#');
    time.sleep(3);
    client.loop_stop();
    client.disconnect();
    exit(0);

def roomba_time():
    rt = datetime.datetime.now() - datetime.datetime(1970, 1, 1);
    return str(int(rt.total_seconds()));
    
print("Server mode");
common_string = '","initiator":"localApp","robot_id":"' + roomba_blid + '","time":';

time.sleep(30);
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
miniserver_host = socket.gethostname();
s.bind((miniserver_host, miniserver_port));
s.listen(10);

while True:
    conn, addr = s.accept();
    data = conn.recv(64);
    conn.close();
    message = data.decode('ascii').rstrip();
    print("Recv: " + message);
    
    if (message.startswith(roomba_prefix)):
        roomba_message = message.replace(roomba_prefix, '');
        
        try:
            client.connect(roomba_host, port = roomba_port);
        except:
            print("! Connect to Roomba");
            continue;
        
        jobs = roomba_jobs.get(roomba_message, '');
        if (jobs != '' or roomba_message == 'start' or roomba_message == 'dock'):
            client.publish('cmd', '{"command":"stop' + common_string + roomba_time() + '}');
            time.sleep(20);
        
        if (jobs != ''):
            jobs_json_array = '';
            
            for job in jobs:
                jobs_json_array += '{"region_id":"' + str(job) + '","type":"rid"},'
            
            client.publish('cmd', '{"command":"start","regions":[' + jobs_json_array[:-1] + '],"ordered":1,"pmap_id":"' + roomba_pmap + common_string + roomba_time() + '}');
        
        else:
            select_all_message = ''
            if (roomba_message == 'start'):
                select_all_message = ',"select_all":true';
            
            client.publish('cmd', '{"command":"' + roomba_message + common_string + roomba_time() + select_all_message + '}');

        client.disconnect();
