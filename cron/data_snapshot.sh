#!/bin/bash
# Daily data snapshot - run at 6 AM

cd /opt/aios || exit 1

source .env 2>/dev/null

python3 data_os/collector.py metric revenue "$(date +%Y-%m-01)" monthly 2>/dev/null

echo "$(date): Daily snapshot completed" >> logs/cron.log