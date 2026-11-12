# SokoRadar USSD and SMS

A USSD menu that works on any phone, and an SMS script that sends spike alerts to subscribers. Both read the final SokoRadar table (forecasts plus alerts), so replies are instant and no model runs here.

## What a user sees

```
SokoRadar: bei za chakula
1. Bei ijayo (Price outlook)
2. Onyo kaunti yangu (Alerts)
3. Jiandikishe SMS
4. Jiondoe SMS
```

1. **Bei ijayo:** choose county, crop and retail or wholesale. Example answer:
   ```
   Mahindi, Bungoma (rejareja)
   Des 2024: KES 48/kg (makadirio)
   Jan 2025: KES 49 (42-56)
   Bei sasa: Kawaida kwa msimu
   ONYO: bei inaweza kupanda zaidi ya 15%
   ```
   The price now, next month's forecast with its 80% range, the ALPS label, the spike alert, and where to buy when there is a suggestion. "(makadirio)" means the price is an estimate.
2. **Onyo kaunti yangu:** choose a county and see every crop with a spike alert next month.
3. **Jiandikishe SMS:** choose a county and agree; the phone number is saved for alert SMS.
4. **Jiondoe SMS:** remove the phone number.

Counties are shown 8 per screen: 9 shows more, 0 goes back. Crops: maize, beans (Rosecoco), sorghum and potatoes (red Irish).

## Files

| File | What it does |
|---|---|
| `app.py` | The web app Africa's Talking calls (`POST /ussd`); `GET /` checks it is up |
| `menu.py` | The menu screens and answers |
| `sokoradar_data.py` | Reads the final table and looks up answers; Kiswahili names |
| `subscribers.py` | Saves and removes SMS subscribers |
| `send_sms_alerts.py` | Sends each subscriber the alerts for their county |
| `simulate.py` | Try the menu in the terminal, like a phone |
| `test_ussd.py` | Checks every county, crop and menu path, and that every screen fits on a phone |
| `data/sokoradar_final.csv` | The final table (forecasts from December 2024 for January to March 2025) |

## Run it on your laptop

```
pip install -r requirements.txt
python test_ussd.py          # should end with "All checks passed"
python simulate.py           # use the menu in the terminal
python app.py                # the web app on http://localhost:5000
```

## Update the data each month

From the repo folder, run the two hand-over scripts, then copy the result here:

```
python notebooks/handover/sokoradar_forecast.py --data data/SokoRadar_County_2006_2024_long.csv --raw sokoradar_raw_data --out sokoradar_forecasts.csv
python notebooks/handover/alerts/sokoradar_alerts.py --data data/SokoRadar_County_2006_2024_long.csv --forecasts sokoradar_forecasts.csv --out ussd/data/sokoradar_final.csv
```

The app picks up the new file by itself; no restart is needed.

## Connect to Africa's Talking (sandbox, free)

1. Sign up at africastalking.com and open the **sandbox**.
2. Make the app reachable from the internet:
   * **For a quick test:** run `python app.py`, then `ngrok http 5000`, and copy the https address ngrok prints.
   * **For the demo:** deploy this folder on Render (free): new Web Service, root directory `ussd`, build command `pip install -r requirements.txt`, start command `gunicorn app:app`.
3. In the sandbox, go to **USSD → Create channel**, pick a code, and set the callback URL to `https://<your address>/ussd`.
4. Open the **simulator**, enter a test phone number, dial the code, and use the menu.

## Send alert SMS

```
python send_sms_alerts.py                 # dry run: shows the messages, sends nothing
```

To send through the sandbox (messages appear in the simulator, not on real phones):

```
export AT_USERNAME=sandbox
export AT_API_KEY=<your sandbox API key>
python send_sms_alerts.py --send
```

Each message fits in one SMS (160 characters), for example:

> SokoRadar Kitui Jan 2025: ONYO bei inaweza kupanda >15%: Mahindi KES 42 (37-48), Viazi KES 47 (35-64).

Real phones need a live Africa's Talking account with a small top up. Send to a real number only with the owner's permission.

## Limits

* The data ends in December 2024, so the forecasts are for January to March 2025.
* Subscribers are saved in a CSV file. On free hosting this file is lost when the app restarts; a real service would use a small database.
* Phone numbers are personal data: they are saved only after the user agrees, used only for alerts, and never committed to GitHub.
* The Kiswahili text needs a check by a native speaker before the demo.
* An alert means higher risk, not a certain price rise.
