# Log Routing Project

This project demonstrates a dynamic UDP log routing architecture using Docker Compose, syslog-ng, a custom Python-based UDP load balancer, and Consul for service discovery.

---

## Project Structure

```
log-routing-project/
├── docker-compose.yaml
├── consul/
│   └── config/
│       ├── syslog1.json
│       └── syslog2.json
├── loadbalancer/
│   ├── Dockerfile
│   └── udp_load_balancer.py
├── logger/
│   ├── Dockerfile
│   └── logger.py
├── syslog/
│   └── syslog-ng.conf
├── health_check.sh
├── restart.sh
```

---

## Step-by-Step Setup Instructions

### 1. Create Project Directory Structure
```bash
mkdir -p log-routing-project/consul/config
mkdir -p log-routing-project/loadbalancer
mkdir -p log-routing-project/logger
mkdir -p log-routing-project/syslog
cd log-routing-project
```

### 2. Add `docker-compose.yaml`
```yaml
version: '3.8'
services:
  logger:
    build: ./logger
    container_name: logger
    depends_on:
      - loadbalancer

  loadbalancer:
    build: ./loadbalancer
    container_name: loadbalancer
    depends_on:
      - consul

  syslog1:
    image: balabit/syslog-ng:latest
    container_name: syslog1
    volumes:
      - ./syslog/syslog-ng.conf:/etc/syslog-ng/syslog-ng.conf
    ports:
      - "514:514/udp"

  syslog2:
    image: balabit/syslog-ng:latest
    container_name: syslog2
    volumes:
      - ./syslog/syslog-ng.conf:/etc/syslog-ng/syslog-ng.conf
    ports:
      - "515:514/udp"

  consul:
    image: consul
    container_name: consul
    ports:
      - "8500:8500"
    command: "agent -dev -client=0.0.0.0"
```

### 3. Add `logger/logger.py`
```python
import socket
import time
import os

host = os.getenv("TARGET", "loadbalancer")
port = 514
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    message = f"<13>{time.strftime('%Y-%m-%d %H:%M:%S')} Logger says hello!"
    sock.sendto(message.encode(), (host, port))
    print(f"Sending: {message}")
    time.sleep(1)
```

### 4. Add `loadbalancer/udp_load_balancer.py`
```python
import socket
import json
import time
import requests
import random

UDP_IP = "0.0.0.0"
UDP_PORT = 514
BUFFER_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

while True:
    try:
        resp = requests.get("http://consul:8500/v1/agent/services")
        services = resp.json()
        syslog_services = [
            (v['Address'], v['Port']) for k, v in services.items() if 'syslog' in v['Tags']
        ]
        if not syslog_services:
            print("No syslog servers found. Waiting...")
            time.sleep(2)
            continue

        data, addr = sock.recvfrom(BUFFER_SIZE)
        target = random.choice(syslog_services)
        print(f"Forwarding to {target}: {data.decode()}")
        sock.sendto(data, target)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
```

### 5. Add Consul Service Definitions (`consul/config/syslog1.json` and `syslog2.json`)
```json
{
  "Name": "syslog",
  "ID": "syslog1",
  "Tags": ["syslog"],
  "Port": 514,
  "Address": "syslog1"
}
```
```json
{
  "Name": "syslog",
  "ID": "syslog2",
  "Tags": ["syslog"],
  "Port": 514,
  "Address": "syslog2"
}
```

### 6. Add `syslog/syslog-ng.conf`
```conf
@version: 3.38
@include "scl.conf"
source s_net { udp(ip(0.0.0.0) port(514)); };
destination d_file { file("/var/log/syslog-ng/messages.log"); };
log { source(s_net); destination(d_file); };
```

### 7. Start Everything
```bash
docker-compose up --build
```

### 8. Register Services to Consul (from inside the consul container)
```bash
curl --request PUT --data @/consul/config/syslog1.json http://localhost:8500/v1/agent/service/register
curl --request PUT --data @/consul/config/syslog2.json http://localhost:8500/v1/agent/service/register
```

---

## ✅ Verifying Project Functionality

### ✅ 1. Are All Service Containers Running?
```bash
docker ps
```
Expected:
- All containers `Up` and `healthy` if healthchecks are defined:
  - logger
  - loadbalancer
  - syslog1
  - syslog2
  - consul

### ✅ 2. Are Syslog Servers Discovered in Consul?
```bash
curl http://localhost:8500/v1/catalog/services
```
Expected output:
```json
{
  "consul": [],
  "syslog": []
}
```
Or use web interface:
👉 http://localhost:8500/ui

### ✅ 3. Is the Load Balancer Forwarding Logs Correctly?
```bash
docker logs log-routing-project_loadbalancer_1 -f
```
Expected output:
```text
Discovered servers: [('syslog1', 514), ('syslog2', 514)]
Forwarding to ('syslog2', 514)
Forwarding to ('syslog1', 514)
```

### ✅ 4. Is the Logger Producing UDP Logs?
```bash
docker logs log-routing-project_logger_1 -f
```
Expected output:
```text
Sending: <13>2025-04-23 19:00:00 Logger says hello!
Sending: <13>2025-04-23 19:00:01 Logger says hello!
```

### ✅ 5. Are Logs Written to Syslog Files?
```bash
docker exec -it log-routing-project_syslog1_1 cat /var/log/syslog-ng/messages.log
docker exec -it log-routing-project_syslog2_1 cat /var/log/syslog-ng/messages.log
```
Expected log samples:
```text
Apr 23 19:00:01 logger Logger says hello!
```

### ✅ 6. (Optional) Can You See Logs via Docker Logs?
If `syslog-ng.conf` is configured with:
```conf
destination d_stdout { file("/dev/stdout"); };
```
Then:
```bash
docker logs log-routing-project_syslog1_1 -f
```
Will show logs in terminal ✅

---

## Summary
This project enables UDP log messages to be distributed dynamically to registered syslog-ng servers using Consul for service discovery and a Python-based custom load balancer. It is designed to be modular and easily expandable.

