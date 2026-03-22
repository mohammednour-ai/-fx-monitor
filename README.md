# CAD FX Monitor 💱

Automated hourly CAD exchange rate monitor that sends WhatsApp updates via CallMeBot.

Tracks **CAD vs USD, GBP, EUR, HKD** — shows current rate, day-open rate, and change.

## Sample WhatsApp Message

```
📊 CAD FX Monitor — 2026-03-21 14:00 UTC

🟢 CAD/USD
   Now:  0.7245
   Open: 0.7230
   Chg:  +0.0015 (+0.21%)

🔴 CAD/GBP
   Now:  0.5712
   Open: 0.5720
   Chg:  -0.0008 (-0.14%)

...
```

## Setup (15 minutes)

### Step 1: Get your ExchangeRate-API key (free)

1. Go to [https://www.exchangerate-api.com/](https://www.exchangerate-api.com/)
2. Sign up with your email
3. Copy your API key from the dashboard

### Step 2: Set up CallMeBot (free)

1. Save the phone number **+34 644 71 81 84** in your contacts
2. Open WhatsApp and send this message to that number:
   ```
   I allow callmebot to send me messages
   ```
3. You'll receive a reply with your **API key** — save it

### Step 3: Create GitHub repo & add secrets

1. Create a new **private** GitHub repository
2. Push this code to it
3. Go to **Settings → Secrets and variables → Actions**
4. Add these 3 **Repository secrets**:

| Secret Name         | Value                                      |
|---------------------|--------------------------------------------|
| `FX_API_KEY`        | Your ExchangeRate-API key                  |
| `WHATSAPP_NUMBER`   | Your phone number with country code (e.g. `12895551234`) |
| `CALLMEBOT_API_KEY` | The API key CallMeBot sent you             |

### Step 4: Enable the workflow

1. Go to the **Actions** tab in your repo
2. Click "I understand my workflows, go ahead and enable them"
3. Click **CAD FX Monitor** in the left sidebar
4. Click **Run workflow** to test it manually

You should receive a WhatsApp message within 30 seconds!

## Customization

### Change monitored currencies

Edit `PAIRS` in `fx_monitor.py`:
```python
PAIRS = ["USD", "GBP", "EUR", "HKD", "SAR", "EGP"]  # Add any you want
```

### Change schedule

Edit the cron in `.github/workflows/fx_monitor.yml`:
```yaml
- cron: '0 9-21 * * 1-5'  # Every hour 9am-9pm UTC, weekdays only
```

### Run only on trading days

```yaml
- cron: '0 13-21 * * 1-5'  # 8am-4pm EST, Mon-Fri
```

## How It Works

1. **GitHub Actions** triggers the script on a cron schedule
2. Script fetches live CAD rates from ExchangeRate-API
3. First run of each day caches rates as the "day open"
4. Subsequent runs compare current vs open and calculate change
5. Formatted message is sent to your WhatsApp via CallMeBot

## Cost

**$0** — all services used are free tier:
- GitHub Actions: 2,000 min/month free (this uses ~1 min/day)
- ExchangeRate-API: 1,500 requests/month free (this uses ~720/month)
- CallMeBot: Free

## Troubleshooting

- **No WhatsApp message?** Run the workflow manually from Actions tab and check the logs
- **CallMeBot not responding?** Re-send the authorization message to their number
- **Wrong rates?** ExchangeRate-API updates every few minutes on the free plan
- **Cache not working?** The day-open resets whenever GitHub can't find a cached file (which is fine — it just uses the current rate as the open)
