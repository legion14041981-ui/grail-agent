# GRAIL AGENT — System Architecture

## Overview

**GRAIL AGENT** is an autonomous trading system with production-grade architecture designed for reliability, observability, and independent operation.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GRAIL AGENT SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           TRADING ENGINE (Core)                     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  - Signal Generation                                │   │
│  │  - Confidence Scoring                               │   │
│  │  - Trade Execution Logic                            │   │
│  │  - P&L Calculation                                  │   │
│  │  - Risk Management                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ▲                                   │
│                         │                                   │
│  ┌─────────────────────┴──────────────────────────────┐   │
│  │         PERSISTENCE LAYER (Supabase)              │   │
│  ├───────────────────────────────────────────────────┤   │
│  │  - Predictions Table                              │   │
│  │  - Trades Table                                   │   │
│  │  - Real-time sync                                 │   │
│  └───────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      CI/CD AUTOMATION (GitHub Actions)             │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  - Scheduled Execution (cron: */5 min)             │   │
│  │  - Artifact Upload (logs)                          │   │
│  │  - Status Reporting                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         CHECKPOINT SYSTEM (Recovery)               │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  - State snapshots (JSON)                          │   │
│  │  - Recovery branches (git)                         │   │
│  │  - Validation workflows                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Trading Engine

**File:** `grail_agent_production.py`

**Responsibilities:**
- Generate trading signals (BUY/SELL/HOLD)
- Score confidence levels (0.6–0.95)
- Execute trades based on thresholds
- Calculate P&L and update bankroll
- Log all operations

**Modes:**
- **Demo:** Virtual trading with simulated P&L
- **Live:** Real trading (not yet implemented)

**Key Methods:**
- `generate_signal()` — Create trading signals
- `execute_trade(signal)` — Execute trade if confidence > 0.70
- `log_prediction_to_supabase(signal)` — Persist prediction
- `log_trade_to_supabase(trade)` — Persist trade result

### 2. Persistence Layer

**Technology:** Supabase (PostgreSQL)

**Tables:**

```sql
-- Predictions table
CREATE TABLE predictions (
  id BIGSERIAL PRIMARY KEY,
  event_name TEXT NOT NULL,
  signal TEXT NOT NULL,
  asset TEXT NOT NULL,
  confidence FLOAT NOT NULL,
  mode TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trades table
CREATE TABLE trades (
  id TEXT PRIMARY KEY,
  profit_loss FLOAT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Configuration:**
- `SUPABASE_URL` — Project URL
- `SUPABASE_KEY` — Anonymous key

### 3. CI/CD Automation

**Workflow:** `.github/workflows/grail_agent_deploy.yml`

**Triggers:**
- **Schedule:** Every 5 minutes (`cron: '*/5 * * * *'`)
- **Push:** On code changes to `main`
- **Manual:** `workflow_dispatch`

**Steps:**
1. Checkout code
2. Setup Python 3.11
3. Cache pip dependencies
4. Install requirements + Playwright
5. Execute trading engine
6. Upload logs as artifacts
7. Report execution status

**Artifacts:**
- `grail_agent.log` — Execution logs (7-day retention)

### 4. Checkpoint System

**Purpose:** State recovery and audit trail

**Structure:**
```
recovery/checkpoint-{N}/
└── .runtime/
    └── checkpoint_{N}.json
```

**Metadata:**
```json
{
  "checkpoint": 20,
  "timestamp": "2025-12-13T05:00:44+03:00",
  "win_rate": 0.75,
  "total_pnl": 137.32,
  "trades": 20,
  "balance": 1151.00,
  "patterns": {
    "CLASSIC": {"trades": 11, "win_rate": 0.727},
    "NEWSEVENT": {"trades": 5, "win_rate": 1.0},
    "VOLEVENT": {"trades": 4, "win_rate": 0.5}
  }
}
```

**Validation:**
- Workflow: `08-checkpoint-validator.yml`
- Manual trigger with checkpoint number
- Validates tag existence and integrity

## Data Flow

```
1. GitHub Actions Trigger (cron: */5 min)
           |
           v
2. Python Environment Setup
           |
           v
3. Load Supabase Credentials (secrets)
           |
           v
4. Execute Trading Engine
           |
           v
5. Generate Signal → Log to Supabase
           |
           v
6. Execute Trade (if confidence > 0.70)
           |
           v
7. Log Trade Result → Supabase
           |
           v
8. Update Bankroll & Calculate P&L
           |
           v
9. Upload Logs as Artifact
           |
           v
10. Report Status & Exit
```

## Deployment Architecture

### Environment: GitHub Actions Runner

**OS:** Ubuntu Latest  
**Python:** 3.11  
**Browser:** Chromium (Playwright)  
**Runtime:** Ephemeral (5-minute intervals)  

### Scalability

- **Horizontal:** Multiple repos with different strategies
- **Vertical:** Increase prediction frequency or bankroll
- **Distributed:** Deploy to dedicated servers (future)

### Resilience

- **Error Handling:** Try-catch in prediction loop
- **Logging:** Comprehensive stdout + file logging
- **Fallback:** Continues on single prediction failure
- **Recovery:** Checkpoint system for state restoration

## Security

### Secrets Management

- `SUPABASE_URL` — Stored in GitHub Secrets
- `SUPABASE_KEY` — Stored in GitHub Secrets
- Never committed to git

### Access Control

- Supabase Row Level Security (RLS)
- GitHub Actions secrets encryption
- Repository-level permissions

## Monitoring

### Logs

- **File:** `grail_agent.log`
- **Format:** Timestamp, level, message
- **Retention:** 7 days (GitHub Artifacts)

### Metrics

- Total trades executed
- Predictions logged
- Win rate
- P&L (absolute and percentage)
- ROI

### Alerts

- GitHub Actions failure notifications
- Manual log review (currently)
- Prometheus/Grafana integration (future)

## Migration History

**Original:** Embedded in [Legion monorepo](https://github.com/legion14041981-ui/Legion)  
**Migrated:** 2025-12-13 21:20 MSK  
**Reason:** Separation of concerns, independent lifecycle  

See [MIGRATION.md](MIGRATION.md) for details.

## Future Enhancements

- [ ] Live trading mode implementation
- [ ] Real-time WebSocket integration
- [ ] Advanced pattern recognition (ML models)
- [ ] Multi-exchange support
- [ ] Prometheus metrics export
- [ ] Grafana dashboards
- [ ] Slack/Discord notifications
- [ ] Backtesting framework
- [ ] Risk management enhancements

---

**Architecture Status:** ✅ PRODUCTION-READY  
**Last Updated:** 2025-12-13  
**Version:** 1.0.0 (Post-Migration)
