# investments-alert-agent

An automated ETF dip alert agent that monitors stock prices daily and sends intelligent Slack notifications when meaningful drops are detected.

Built with GitHub Actions + Claude API (Anthropic). Runs entirely in the cloud — no server or local machine needed.

---

## How It Works

Every weekday at market close (5pm ET), the agent:

1. Fetches the latest VOO closing price via Yahoo Finance
2. Compares it against the tracked recent peak (stored in `state.json`)
3. Calculates the % drop and determines the alert tier:
   - **< 3% drop** → silent daily update posted to Slack (no notification)
   - **3–5% drop** → 🟡 Heads-Up alert with AI-generated market summary
   - **8%+ drop** → 🚨 Strong Dip alert with AI-generated market summary
4. If a new all-time high is reached, the peak is automatically updated in `state.json`

For Tier 1 and Tier 2 alerts, Claude (Haiku) generates a 2-sentence market context summary to help you make an informed decision. No trades are executed — all buy decisions are yours.

---

## Example Slack Messages

**Normal day:**
```
VOO Daily Update — 2026-05-07
Closed: $668.00 | Recent Peak: $675.00 | Drop: -1.0%
Status: ✅ Within normal range.
```

**Tier 1 — Heads-Up:**
```
@here 🟡 VOO Heads-Up — 2026-05-07
Closed: $651.00 | Recent Peak: $675.00 | Drop: -3.6%

[2-sentence Claude summary of market context]

A moderate dip has been detected. Review and consider your next move.
```

**Tier 2 — Strong Dip:**
```
@here 🚨 VOO Strong Dip — 2026-05-07
Closed: $615.00 | Recent Peak: $675.00 | Drop: -8.9%

[2-sentence Claude summary of market context]

A significant dip has been detected. Review and consider your next move.
```

---

## Setup

### 1. Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/investments-alert-agent.git
cd investments-alert-agent
```

### 2. Set your starting peak price

Edit `state.json` and set `recent_peak` to VOO's current price:

```json
{
  "recent_peak": 675.00,
  "last_updated": "2026-05-07"
}
```

### 3. Create a Slack Incoming Webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it (e.g. "VOO Alert"), select your workspace → **Create App**
3. Go to **Incoming Webhooks** → toggle **On** → **Add New Webhook to Workspace**
4. Select a channel (e.g. `#investment-alerts`) → **Allow**
5. Copy the Webhook URL (starts with `https://hooks.slack.com/services/...`)

### 4. Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-...`)

> The Claude API is only called on Tier 1 and Tier 2 alert days — typical usage cost is minimal (fractions of a cent per call).

### 5. Add GitHub Secrets

In your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret name | Value |
|---|---|
| `SLACK_WEBHOOK_URL` | Your Slack webhook URL |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

These are never stored in the repo — GitHub injects them only at runtime.

### 6. Enable GitHub Actions

GitHub Actions is enabled by default on public repos. The workflow runs automatically every weekday at 9pm UTC (5pm ET).

To run it manually at any time: go to **Actions** → **VOO Alert Monitor** → **Run workflow**.

---

## Customizing Thresholds

To adjust the dip thresholds, edit these lines in `monitor.py`:

```python
if drop_pct >= 8:    # Tier 2 — Strong Dip
    tier = 2
elif drop_pct >= 3:  # Tier 1 — Heads-Up
    tier = 1
```

To monitor a different ETF, change the ticker in `monitor.py`:

```python
ticker = yf.Ticker("VOO")  # Change to QQQ, VTI, etc.
```

---

## Tech Stack

- **GitHub Actions** — cloud scheduler, no server needed
- **yfinance** — free Yahoo Finance price data
- **Anthropic Claude API (Haiku)** — AI market summary on dip days only
- **Slack Incoming Webhooks** — alert delivery

---

## License

MIT
