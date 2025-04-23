#!/bin/bash
docker-compose down -v
docker system prune -af  # <-- Tüm eski imajları siler (önemli!)
docker-compose build --no-cache
docker-compose up -d
