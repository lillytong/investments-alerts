# investments-alerts

A scheduled ETF price monitor that sends daily Slack alerts with AI-generated market context. Built with GitHub Actions + Claude API — runs entirely in the cloud, no server or local machine needed.

---

## How It Works

Every weekday at 9am CET, the workflow:

1. Fetches the latest VOO closing price via Yahoo Finance
2. Compares price against the tracked recent peak (stored in `state.json`)
3. Calculates the % drop and determines the alert tier:
   - **< 3% drop** → silent daily Slack update, no Claude call
   - **3–5% drop** → 🟡 Heads-Up alert with 2-sentence Sonnet summary
   - **8%+ drop** → 🚨 Strong Dip alert with 2-sentence Sonnet summary
4. If a new all-time high is reached, the peak auto-updates in `state.json`

On dip days, Claude Sonnet fetches the top 10 Yahoo Finance headlines and generates a grounded 2-sentence market summary before you decide whether to act.

---

## Example Slack Messages

**Normal day (no ping, no AI call):**
```
*VOO Daily Update — 2026-05-07*
Closed: $668.00 | Recent Peak: $675.00 | Drop: -1.0%
Status: ✅ Within normal range.
```

**Tier 1 — Heads-Up (pings you):**
```
@here 🟡 VOO Heads-Up — 2026-05-07
Closed: $651.00 | Recent Peak: $675.00 | Drop: -3.6%

_The pullback reflects broad risk-off sentiment following hawkish Fed commentary; for a long-term index investor, this remains within normal volatility._

A moderate dip has been detected. Review and consider your next move.
```

**Tier 2 — Strong Dip (pings you):**
```
@here 🚨 VOO Strong Dip — 2026-05-07
Closed: $615.00 | Recent Peak: $675.00 | Drop: -8.9%

_The decline is driven by a combination of rising yields and growth fears; historically, S&P 500 corrections of this magnitude have fully recovered within 6–12 months._

A significant dip has been detected. Review and consider your next move.
```

---

## Setup

### 1. Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/investments-alerts.git
cd investments-alerts
```

### 2. Set your starting peak price

Edit `state.json` with VOO's current price as your baseline:

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

### 5. Add GitHub Secrets

In your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret name | Value |
|---|---|
| `SLACK_WEBHOOK_URL` | Your Slack webhook URL |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

These are never stored in the repo — GitHub injects them only at runtime.

### 6. (Optional) Local development

Create a `.env` file (already in `.gitignore` — never committed):

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Then run locally:

```bash
pip install yfinance anthropic requests python-dotenv
python monitor.py
```

---

## AI-Powered Market Context

Claude is called once per run to generate a grounded market summary based on **real Yahoo Finance headlines** fetched at runtime — not hallucinated context.

| Day type | Model | Summary |
|---|---|---|
| Normal (< 3% drop) | None | No AI call — just price data |
| Tier 1 (3–5% drop) | Claude Sonnet | 2 sentences — dip context + investor perspective |
| Tier 2 (8%+ drop) | Claude Sonnet | 2 sentences — dip context + investor perspective |

**Cost:** Sonnet is called only on meaningful dip days. Total monthly cost is typically under $1.

---

## Customizing

**Change dip thresholds** in `monitor.py`:

```python
if drop_pct >= 8:    # Tier 2 — Strong Dip
    tier = 2
elif drop_pct >= 3:  # Tier 1 — Heads-Up
    tier = 1
```

**Monitor a different ETF:**

```python
ticker = yf.Ticker("VOO")  # Change to QQQ, VTI, SPY, etc.
```

**Change the schedule** in `.github/workflows/voo-monitor.yml`:

```yaml
cron: '0 7 * * 1-5'  # 7am UTC = 9am CET — change to suit your timezone
```

---

## Tech Stack

- **GitHub Actions** — free cloud scheduler, no server needed
- **yfinance** — free Yahoo Finance price + news data
- **Anthropic Claude API** — Haiku for daily summaries, Sonnet for dip alerts
- **Slack Incoming Webhooks** — alert delivery

---

## License

MIT
