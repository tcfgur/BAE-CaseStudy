import socket
import random
import requests

UDP_IP = "0.0.0.0"
UDP_PORT = 514
BUFFER_SIZE = 8192

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

def get_syslog_servers():
    try:
        r = requests.get("http://consul:8500/v1/catalog/service/syslog")
        servers = [
            (
                s['ServiceAddress'] if s['ServiceAddress'] else s['Address'],
                s['ServicePort']
            )
            for s in r.json()
        ]
        print(f"Discovered servers: {servers}", flush=True)
        return servers
    except Exception as e:
        print(f"Failed to get syslog servers: {e}", flush=True)
        return []

print("UDP Load Balancer started", flush=True)

while True:
    data, addr = sock.recvfrom(BUFFER_SIZE)
    servers = get_syslog_servers()
    if servers:
        target = random.choice(servers)
        print(f"Forwarding to {target}", flush=True)
        forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forward_sock.sendto(data, target)

