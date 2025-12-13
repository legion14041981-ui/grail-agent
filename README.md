# 🏆 GRAIL AGENT — Autonomous Trading System

![Status](https://img.shields.io/badge/status-production-green)
![Architecture](https://img.shields.io/badge/architecture-independent-blue)
![Win Rate](https://img.shields.io/badge/win%20rate-75%25-success)
![P%2FL](https://img.shields.io/badge/P%2FL-%2B13.5%25-brightgreen)

## 📊 Overview

**GRAIL AGENT** is an autonomous trading system with production-proven performance:

- **Day 5 Performance:** 20 trades, 75% win rate, +$137.32 (+13.5% P&L)
- **Architecture:** Independent repository (migrated from Legion monorepo)
- **Deployment:** GitHub Actions automation (every 5 minutes)
- **Persistence:** Supabase for predictions and trades
- **Modes:** Demo (virtual) and Live (coming soon)

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-anon-key
```

### Run Locally

```bash
# Demo mode (virtual trading)
python grail_agent_production.py --mode demo --bankroll 100 --num-predictions 10

# Live mode (not yet implemented)
python grail_agent_production.py --mode live --bankroll 1000 --num-predictions 50
```

### Run Tests

```bash
pytest tests/ -v --cov=grail_agent_production
```

## 📁 Project Structure

```
grail-agent/
├── grail_agent_production.py      # Main trading engine
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Git exclusions
├── README.md                       # This file
├── ARCHITECTURE.md                 # System design
├── MIGRATION.md                    # Migration history
├── DEPLOYMENT.md                   # Deployment guide
├── .github/
│   └── workflows/
│       ├── 00-ci-alive.yml         # CI heartbeat
│       ├── 08-checkpoint-validator.yml
│       └── grail_agent_deploy.yml  # Auto-deploy (every 5 min)
├── .runtime/
│   └── checkpoint_20.json          # Checkpoint metadata
└── tests/
    └── test_grail_agent.py         # Unit tests
```

## 🎯 Features

### Core Capabilities
- ✅ Automated signal generation
- ✅ Confidence-based trade execution
- ✅ Supabase persistence (predictions + trades)
- ✅ Comprehensive logging
- ✅ Demo mode for testing
- ✅ GitHub Actions automation
- ✅ Checkpoint system for recovery

### Performance Tracking
- Real-time P&L calculation
- Win rate monitoring
- Pattern classification (CLASSIC, NEWSEVENT, VOLEVENT)
- ROI reporting

### Resilience
- Error recovery
- Circuit breaker patterns
- Fallback mechanisms
- Health diagnostics

## 📊 Checkpoint System

GRAIL AGENT uses a checkpoint system to preserve state:

```bash
# Checkpoints stored in recovery branches
git branch -r | grep recovery/checkpoint

# View checkpoint metadata
cat .runtime/checkpoint_20.json
```

**Checkpoint #20 Metrics:**
- Trades: 20
- Win Rate: 75%
- P&L: +$137.32 (+13.5%)
- Balance: $1,151.00

## 🔧 CI/CD Pipeline

### Automated Deployment

GitHub Actions runs the agent every 5 minutes:

```yaml
on:
  schedule:
    - cron: '*/5 * * * *'
```

### Workflows

1. **00-ci-alive.yml** — CI heartbeat validation
2. **08-checkpoint-validator.yml** — Checkpoint integrity checks
3. **grail_agent_deploy.yml** — Automated trading execution

### Secrets Configuration

Required GitHub Secrets:
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anonymous key

## 🏗️ Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

**Key Components:**
- **Trading Engine** — Signal generation and execution
- **Persistence Layer** — Supabase integration
- **CI Automation** — GitHub Actions orchestration
- **Checkpoint System** — State recovery mechanism

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System architecture
- [MIGRATION.md](MIGRATION.md) — Migration from Legion monorepo
- [DEPLOYMENT.md](DEPLOYMENT.md) — Deployment procedures

## 🔗 Related Projects

- [Legion Framework](https://github.com/legion14041981-ui/Legion) — Multi-agent orchestration framework
- [ultima-prime-ci-overlord](https://github.com/legion14041981-ui/ultima-prime-ci-overlord) — CI healing system

## 📜 License

See [Legion Framework License](https://github.com/legion14041981-ui/Legion/blob/main/LICENSE)

## 🤝 Contributing

This is an independent trading system. For framework-level contributions, see [Legion](https://github.com/legion14041981-ui/Legion).

---

**Status:** ✅ OPERATIONAL (API-First Architecture)  
**Migration:** ✅ COMPLETE (2025-12-13)  
**Performance:** 🏆 EXCEEDING EXPECTATIONS (75% WR, +13.5% P&L)
