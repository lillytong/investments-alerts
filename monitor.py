import yfinance as yf
import json
import os
import requests
from datetime import datetime
import anthropic

STATE_FILE = "state.json"


def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_voo_price():
    ticker = yf.Ticker("VOO")
    hist = ticker.history(period="1d")
    return round(hist["Close"].iloc[-1], 2)


def send_slack_message(webhook_url, message):
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()


def get_claude_summary(current_price, recent_peak, drop_pct, tier):
    client = anthropic.Anthropic()

    if tier == 0:
        prompt = (
            f"VOO (S&P 500 ETF) closed at ${current_price:.2f} yesterday, "
            f"down {drop_pct:.1f}% from its recent peak of ${recent_peak:.2f}. "
            f"In exactly 2 sentences: briefly summarize yesterday's general US market mood "
            f"and any notable macro context. Be factual and concise."
        )
    else:
        prompt = (
            f"VOO (S&P 500 ETF) has dropped {drop_pct:.1f}% from its recent peak of "
            f"${recent_peak:.2f} to ${current_price:.2f} yesterday. "
            f"This is a {'moderate' if tier == 1 else 'significant'} dip. "
            f"In exactly 2 sentences: first summarize the likely market context for this drop, "
            f"then give a brief perspective for a long-term S&P 500 index investor. "
            f"Be factual and concise, not alarmist."
        )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def main():
    slack_webhook = os.environ["SLACK_WEBHOOK_URL"]

    state = load_state()
    recent_peak = state["recent_peak"]
    current_price = get_voo_price()
    today = datetime.now().strftime("%Y-%m-%d")

    # Update peak if new high
    if current_price > recent_peak:
        recent_peak = current_price
        state["recent_peak"] = recent_peak
        state["last_updated"] = today
        save_state(state)

    # Calculate % drop from recent peak
    drop_pct = ((recent_peak - current_price) / recent_peak) * 100

    # Determine alert tier
    if drop_pct >= 8:
        tier = 2
    elif drop_pct >= 3:
        tier = 1
    else:
        tier = 0

    if tier == 0:
        summary = get_claude_summary(current_price, recent_peak, drop_pct, tier)
        message = (
            f"*VOO Daily Update — {today}*\n"
            f"Closed: ${current_price:.2f} | Recent Peak: ${recent_peak:.2f} | Drop: -{drop_pct:.1f}%\n"
            f"Status: ✅ Within normal range.\n\n"
            f"{summary}"
        )
    else:
        summary = get_claude_summary(current_price, recent_peak, drop_pct, tier)

        if tier == 1:
            message = (
                f"@here 🟡 *VOO Heads-Up — {today}*\n"
                f"Closed: ${current_price:.2f} | Recent Peak: ${recent_peak:.2f} | Drop: -{drop_pct:.1f}%\n\n"
                f"{summary}\n\n"
                f"A moderate dip has been detected. Review and consider your next move."
            )
        else:
            message = (
                f"@here 🚨 *VOO Strong Dip — {today}*\n"
                f"Closed: ${current_price:.2f} | Recent Peak: ${recent_peak:.2f} | Drop: -{drop_pct:.1f}%\n\n"
                f"{summary}\n\n"
                f"A significant dip has been detected. Review and consider your next move."
            )

    send_slack_message(slack_webhook, message)
    print(f"Alert sent. Tier: {tier}, Price: ${current_price:.2f}, Drop: -{drop_pct:.1f}%")


if __name__ == "__main__":
    main()
