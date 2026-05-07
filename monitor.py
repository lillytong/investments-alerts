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


def get_market_news(max_headlines=10):
    ticker = yf.Ticker("VOO")
    raw_news = ticker.news or []
    print(f"Raw news count: {len(raw_news)}")
    if raw_news:
        print(f"Sample news item keys: {list(raw_news[0].keys())}")

    headlines = []
    for item in raw_news[:max_headlines]:
        # yfinance news structure varies by version — try both formats
        content = item.get("content", {})
        title = content.get("title") or item.get("title", "")
        summary = content.get("summary") or item.get("summary", "")
        if title:
            headlines.append(f"- {title}: {summary}" if summary else f"- {title}")

    result = "\n".join(headlines) if headlines else "No recent news available."
    print(f"News context:\n{result}")
    return result


def send_slack_message(webhook_url, message):
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()


def get_claude_summary(current_price, recent_peak, drop_pct, tier, news_context):
    client = anthropic.Anthropic()
    news_block = f"Recent market headlines:\n{news_context}"

    if tier == 0:
        prompt = (
            f"VOO (S&P 500 ETF) closed at ${current_price:.2f} yesterday, "
            f"down {drop_pct:.1f}% from its recent peak of ${recent_peak:.2f}.\n\n"
            f"{news_block}\n\n"
            f"Based on these headlines, write exactly 1 sentence summarizing yesterday's "
            f"US market mood. Be factual and concise."
        )
        model = "claude-haiku-4-5-20251001"
        max_tokens = 80
    else:
        prompt = (
            f"VOO (S&P 500 ETF) dropped {drop_pct:.1f}% from its recent peak of "
            f"${recent_peak:.2f} to ${current_price:.2f} yesterday. "
            f"This is a {'moderate' if tier == 1 else 'significant'} dip.\n\n"
            f"{news_block}\n\n"
            f"Based on these headlines, write exactly 2 sentences: first explain the likely "
            f"market context for this drop, then give a brief perspective for a long-term "
            f"S&P 500 index investor. Be factual and concise, not alarmist."
        )
        model = "claude-sonnet-4-6"
        max_tokens = 150

    try:
        print(f"Calling Claude ({model})...")
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = message.content[0].text
        print(f"Claude summary: {summary}")
        return summary
    except Exception as e:
        print(f"Claude API error: {e}")
        return "_(Market summary unavailable)_"


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

    # Fetch news and generate summary for all tiers
    news_context = get_market_news(max_headlines=10)
    summary = get_claude_summary(current_price, recent_peak, drop_pct, tier, news_context)

    if tier == 0:
        message = (
            f"*VOO Daily Update — {today}*\n"
            f"Closed: ${current_price:.2f} | Recent Peak: ${recent_peak:.2f} | Drop: -{drop_pct:.1f}%\n"
            f"Status: ✅ Within normal range.\n\n"
            f"_{summary}_"
        )
    elif tier == 1:
        message = (
            f"@here 🟡 *VOO Heads-Up — {today}*\n"
            f"Closed: ${current_price:.2f} | Recent Peak: ${recent_peak:.2f} | Drop: -{drop_pct:.1f}%\n\n"
            f"_{summary}_\n\n"
            f"A moderate dip has been detected. Review and consider your next move."
        )
    else:
        message = (
            f"@here 🚨 *VOO Strong Dip — {today}*\n"
            f"Closed: ${current_price:.2f} | Recent Peak: ${recent_peak:.2f} | Drop: -{drop_pct:.1f}%\n\n"
            f"_{summary}_\n\n"
            f"A significant dip has been detected. Review and consider your next move."
        )

    send_slack_message(slack_webhook, message)
    print(f"Alert sent. Tier: {tier}, Price: ${current_price:.2f}, Drop: -{drop_pct:.1f}%")


if __name__ == "__main__":
    main()
