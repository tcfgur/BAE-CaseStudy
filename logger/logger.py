import socket, time

UDP_IP = "loadbalancer"
UDP_PORT = 514

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    msg = f"<13>{time.strftime('%Y-%m-%d %H:%M:%S')} Logger says hello!"
    print(f"Sending: {msg}", flush=True)
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))
    time.sleep(1)

