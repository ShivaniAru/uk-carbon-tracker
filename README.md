# UK Grid Carbon Tracker

Tracks how green UK electricity is, every 30 minutes, and finds the best times to use power.

**Data:** National Grid ESO Carbon Intensity API (free, no key).

## Run it
```bash
pip install -r requirements.txt
python collector.py backfill      # one-time: last 13 days of history
streamlit run dashboard.py
python collector.py               # run every 30 min to keep it live
```

## Key findings
_Fill these in after exploring your data (add real numbers):_
1. ...
2. ...
3. ...

## Credits
Carbon Intensity API by National Grid ESO and the University of Oxford.
