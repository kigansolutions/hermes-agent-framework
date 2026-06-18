#!/bin/bash
# Daily brief generation - run at 7 AM

cd /opt/aios || exit 1

source .env 2>/dev/null

python3 -c "
import sys
sys.path.insert(0, '.')
from intelligence.engine import generate_brief_data, save_brief
import json

# Generate brief data and save
data = generate_brief_data()
save_brief('Daily brief generated: ' + json.dumps(data.get('tasks', {})))

print('Daily brief generated')
" >> logs/cron.log 2>&1

echo "$(date): Daily brief completed" >> logs/cron.log