#!/bin/bash

set -e

echo "🔍 Checking Docker containers..."

containers=("logger" "loadbalancer" "syslog1" "syslog2" "consul")

for service in "${containers[@]}"; do
  if ! docker ps --format '{{.Names}}' | grep -q "log-routing-project_${service}_1"; then
    echo "❌ Container '${service}' is not running!"
    exit 1
  else
    echo "✅ ${service} is running"
  fi
done

echo "🌐 Checking Consul service discovery..."

services=$(curl -s http://localhost:8500/v1/catalog/services | jq -r 'keys[]' | grep syslog || true)

if [[ "$services" == *"syslog"* ]]; then
  echo "✅ Consul discovered syslog services"
else
  echo "❌ Consul could not discover syslog services"
  exit 1
fi

echo "📤 Sending test UDP log to load balancer..."

echo "<13>$(date) test log from health check" | nc -u -w1 127.0.0.1 514
sleep 2

echo "📥 Checking syslog servers for the test log..."

found=false
for srv in syslog1 syslog2; do
  if docker exec log-routing-project_${srv}_1 grep -q "test log from health check" /var/log/syslog-ng/messages.log; then
    echo "✅ Log found in ${srv}"
    found=true
  fi
done

if [ "$found" = false ]; then
  echo "❌ Log not found in any syslog server"
  exit 1
fi

echo "🎉 Health check passed!"

