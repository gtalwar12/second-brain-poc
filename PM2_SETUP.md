# PM2 Setup for Second Brain

The Second Brain orchestrator is now running as a persistent PM2 service.

## Service Configuration

- **Service Name**: `second-brain`
- **Polling Interval**: 10 seconds (reduced from 20 seconds)
- **Auto-restart**: Enabled
- **Boot Startup**: Enabled via macOS LaunchAgent

## PM2 Commands

### View Status
```bash
pm2 status second-brain
```

### View Logs
```bash
# Live logs
pm2 logs second-brain

# Last 100 lines
pm2 logs second-brain --lines 100

# Error logs only
pm2 logs second-brain --err
```

### Restart Service
```bash
pm2 restart second-brain
```

### Stop Service
```bash
pm2 stop second-brain
```

### Start Service (if stopped)
```bash
pm2 start second-brain
```

### Monitor Resources
```bash
pm2 monit
```

### View Detailed Info
```bash
pm2 show second-brain
```

## Log Files

Logs are stored in `/Users/home-mini/workspace/second-brain-poc/logs/`:
- `pm2-out.log` - Standard output
- `pm2-error.log` - Error output
- `pm2-combined.log` - Combined logs

## Health Check

Test the service health:
```bash
curl http://localhost:8898/health
```

Expected response:
```json
{
  "status": "running",
  "reminders_processed": 0,
  "notes_processed": 0
}
```

## Configuration Files

- **PM2 Config**: `ecosystem.config.js`
- **Launch Agent**: `~/Library/LaunchAgents/pm2.home-mini.plist`
- **PM2 Process List**: `~/.pm2/dump.pm2`

## Auto-Start on Boot

The service is configured to start automatically when the system boots via:
1. PM2's saved process list (`pm2 save`)
2. macOS LaunchAgent registered in `~/Library/LaunchAgents/`

To verify auto-start is configured:
```bash
ls -la ~/Library/LaunchAgents/pm2.home-mini.plist
```

## Troubleshooting

### Service not starting
```bash
# Check logs for errors
pm2 logs second-brain --err --lines 50

# Restart the service
pm2 restart second-brain

# If still failing, delete and recreate
pm2 delete second-brain
pm2 start ecosystem.config.js
pm2 save
```

### Check Python virtualenv
The service uses the virtualenv at `./venv/bin/python3`. If the virtualenv is missing:
```bash
cd ~/workspace/second-brain-poc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pm2 restart second-brain
```

### Port 8898 in use
If port 8898 is already in use, update the port in `orchestrator.py:297` and restart:
```bash
pm2 restart second-brain
```

## Performance

- **Memory**: ~50MB
- **CPU**: <1% idle, ~10-20% during processing
- **Uptime**: Automatically restarted on crashes
- **Max Restarts**: 10 within the min uptime window
- **Restart Delay**: 4 seconds

## Changes Made

1. ✅ Installed PM2 (v6.0.13 already present)
2. ✅ Created `ecosystem.config.js` with service configuration
3. ✅ Reduced polling interval from 20s to 10s in `orchestrator.py`
4. ✅ Started service via `pm2 start ecosystem.config.js`
5. ✅ Saved PM2 process list with `pm2 save`
6. ✅ Verified auto-start configuration (LaunchAgent already exists)
