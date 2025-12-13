# GRAIL AGENT — Deployment Guide

## Deployment Environments

### 1. GitHub Actions (Current)

**Status:** ✅ OPERATIONAL

**Trigger:** Automated every 5 minutes via cron schedule

**Setup:**
1. Repository already configured
2. Secrets already set (SUPABASE_URL, SUPABASE_KEY)
3. Workflow: `.github/workflows/grail_agent_deploy.yml`

**Monitoring:**
```bash
# View workflow runs
https://github.com/legion14041981-ui/grail-agent/actions

# Download logs
gh run list --workflow=grail_agent_deploy.yml
gh run download <run-id>
```

### 2. Local Development

**Setup:**
```bash
# Clone repository
git clone https://github.com/legion14041981-ui/grail-agent.git
cd grail-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run demo mode
python grail_agent_production.py --mode demo --bankroll 100 --num-predictions 10
```

### 3. Docker (Future)

**Dockerfile (planned):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    playwright install-deps

COPY . .

ENTRYPOINT ["python", "grail_agent_production.py"]
CMD ["--mode", "demo", "--bankroll", "100", "--num-predictions", "10"]
```

**Usage:**
```bash
docker build -t grail-agent .
docker run -e SUPABASE_URL=$SUPABASE_URL -e SUPABASE_KEY=$SUPABASE_KEY grail-agent
```

### 4. Dedicated Server (Future)

**Requirements:**
- Ubuntu 22.04+ or similar
- Python 3.11+
- Systemd for service management
- Reverse proxy (optional, for monitoring)

**Systemd Service:**
```ini
[Unit]
Description=GRAIL Agent Trading System
After=network.target

[Service]
Type=simple
User=grail
WorkingDirectory=/opt/grail-agent
Environment="SUPABASE_URL=https://your-project.supabase.co"
Environment="SUPABASE_KEY=your-anon-key"
ExecStart=/opt/grail-agent/venv/bin/python grail_agent_production.py --mode live --bankroll 1000 --num-predictions 100
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

## Configuration Management

### Environment Variables

**Required:**
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anonymous key

**Optional:**
- `LOG_LEVEL` — Logging level (INFO, DEBUG, WARNING, ERROR)
- `BANKROLL` — Initial bankroll (overrides CLI)
- `MODE` — Trading mode (demo, live)

### Secrets Management

**GitHub Actions:**
```bash
# Set secrets via GitHub UI or CLI
gh secret set SUPABASE_URL --body "https://your-project.supabase.co"
gh secret set SUPABASE_KEY --body "your-anon-key"
```

**Local Development:**
```bash
# Use .env file (not committed)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

**Production Server:**
```bash
# Use environment variables or secrets manager
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"

# Or use systemd EnvironmentFile
EnvironmentFile=/etc/grail-agent/secrets.env
```

## Monitoring

### Logs

**GitHub Actions:**
- Artifact: `grail-logs-{run-number}`
- Retention: 7 days
- Download via Actions UI or `gh` CLI

**Local:**
- File: `grail_agent.log`
- Rotation: Manual (use logrotate)

**Production:**
```bash
# Systemd journal
journalctl -u grail-agent -f

# File-based (if configured)
tail -f /var/log/grail-agent/grail_agent.log
```

### Metrics

**Current:** Manual log analysis

**Future:** Prometheus + Grafana
```python
# Add to grail_agent_production.py
from prometheus_client import start_http_server, Counter, Gauge

trades_counter = Counter('grail_trades_total', 'Total trades executed')
pnl_gauge = Gauge('grail_pnl', 'Current P&L')
win_rate_gauge = Gauge('grail_win_rate', 'Current win rate')
```

### Alerts

**GitHub Actions:**
- Workflow failure notifications (email/Slack)
- Configure in repository settings

**Production:**
- Systemd failure alerts
- Prometheus Alertmanager rules
- Slack/Discord webhooks

## Scaling

### Horizontal Scaling

**Multiple Strategies:**
```bash
# Deploy multiple repos with different strategies
grail-agent-conservative/
grail-agent-aggressive/
grail-agent-balanced/
```

**Multiple Exchanges:**
```bash
# One instance per exchange
grail-agent-binance/
grail-agent-coinbase/
grail-agent-kraken/
```

### Vertical Scaling

**Increase Frequency:**
```yaml
# .github/workflows/grail_agent_deploy.yml
schedule:
  - cron: '*/1 * * * *'  # Every 1 minute
```

**Increase Bankroll:**
```bash
python grail_agent_production.py --mode live --bankroll 10000
```

## Backup & Recovery

### Checkpoint System

**Create Checkpoint:**
```bash
# Manual checkpoint creation
git checkout -b recovery/checkpoint-$(date +%s)
echo '{"checkpoint": 50, ...}' > .runtime/checkpoint_50.json
git add .runtime/checkpoint_50.json
git commit -m "checkpoint: #50 state snapshot"
git push origin recovery/checkpoint-$(date +%s)
```

**Restore from Checkpoint:**
```bash
# List checkpoints
git branch -r | grep recovery/checkpoint

# Checkout specific checkpoint
git checkout recovery/checkpoint-20

# View metadata
cat .runtime/checkpoint_20.json
```

### Supabase Backup

**Export Data:**
```bash
# Use Supabase CLI or pg_dump
supabase db dump > backup_$(date +%Y%m%d).sql
```

**Restore Data:**
```bash
supabase db reset
psql -h db.your-project.supabase.co -U postgres -d postgres -f backup_20251213.sql
```

## Troubleshooting

### Common Issues

**1. Supabase Connection Failed**
```bash
# Check credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
curl -X GET "$SUPABASE_URL/rest/v1/predictions?limit=1" \
  -H "apikey: $SUPABASE_KEY"
```

**2. Playwright Browser Not Found**
```bash
# Reinstall browser
playwright install chromium
playwright install-deps
```

**3. GitHub Actions Failure**
```bash
# Check workflow logs
gh run list --workflow=grail_agent_deploy.yml --limit 5
gh run view <run-id> --log

# Re-run failed job
gh run rerun <run-id>
```

### Debug Mode

**Enable DEBUG Logging:**
```python
# In grail_agent_production.py
logging.basicConfig(level=logging.DEBUG)  # Change from INFO
```

**Dry Run (No Supabase):**
```bash
# Unset credentials to run without DB
unset SUPABASE_URL SUPABASE_KEY
python grail_agent_production.py --mode demo
```

## Security

### Best Practices

- ✅ Never commit `.env` or secrets
- ✅ Use GitHub Secrets for CI/CD
- ✅ Rotate Supabase keys periodically
- ✅ Enable Supabase Row Level Security (RLS)
- ✅ Limit API key permissions (read/write only tables needed)
- ✅ Use HTTPS for all external connections
- ✅ Monitor for unusual trading patterns

### Supabase RLS Example

```sql
-- Enable RLS on predictions table
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Allow service role to insert
CREATE POLICY "Service role can insert"
  ON predictions FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Allow anon to read (for monitoring)
CREATE POLICY "Anon can read"
  ON predictions FOR SELECT
  TO anon
  USING (true);
```

## Rollout Checklist

### Pre-Deployment

- [ ] Code reviewed and tested
- [ ] Dependencies up to date
- [ ] Secrets configured
- [ ] Documentation updated
- [ ] Checkpoint created (if applicable)

### Deployment

- [ ] Merge to `main` branch
- [ ] GitHub Actions workflow triggered
- [ ] First run successful
- [ ] Logs reviewed
- [ ] Supabase data validated

### Post-Deployment

- [ ] Monitor first 5 runs
- [ ] Verify P&L calculations
- [ ] Check error rates
- [ ] Review performance metrics
- [ ] Update status documentation

---

**Deployment Status:** ✅ OPERATIONAL (GitHub Actions)  
**Last Updated:** 2025-12-13  
**Next Review:** 2025-12-20
