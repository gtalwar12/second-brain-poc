module.exports = {
  apps: [{
    name: 'second-brain',
    script: 'orchestrator.py',
    interpreter: './venv/bin/python3',
    cwd: '/Users/home-mini/workspace/second-brain-poc',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      PYTHONUNBUFFERED: '1'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_file: './logs/pm2-combined.log',
    time: true,
    merge_logs: true,
    max_restarts: 10,
    min_uptime: '10s',
    restart_delay: 4000
  }]
};
