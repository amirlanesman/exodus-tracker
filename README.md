# Exodus Sailing Tracker

Live map tracking dashboard designed for Garmin inReach integration, utilizing Windy.com Maps API and automated GitHub Actions to minimize hosting complexity.

## How it works

1. **Frontend App**: `index.html` loads data locally from `data.kml` and plots it over an interactive Windy weather map using Leaflet. 
2. **Data Automation**: A GitHub Action (`.github/workflows/update_data.yml`) runs every 30 minutes to fetch the latest tracking feed from Garmin MapShare.
3. **Data Minification**: Garmin feeds grow massively over time because every position update carries an extensive `<ExtendedData>` block. To prevent performance lag and excessive network payload, `process_kml.py` strips out older individual `<Point>` updates while preserving the continuous sailed route `<LineString>` and the most recent `<Point>` for live telemetry.

## Usage & Development

### Using the Processing Script

If you are downloading a Garmin KML feed manually and want to minify it before committing to the repository, you can run the provided Python script:

```bash
# Syntax: python process_kml.py <input> <output>
python3 process_kml.py my_downloaded_feed.kml data.kml
```

The script works locally using Python's standard libraries—no external dependencies are required.

### Local Development

Since the site performs an XML fetch request to `data.kml`, running `index.html` directly from a `file://` path might trigger CORS/fetch errors in modern browsers.

Run a quick local web server from your terminal:
```bash
python3 -m http.server 8765
```
Then visit: http://localhost:8765

### Configuration

- **API Keys**: Make sure to insert your own Windy Map API Key in `index.html`.
- **Feed URL**: Update the Garmin Share URL inside `.github/workflows/update_data.yml` to target your specific tracker.
