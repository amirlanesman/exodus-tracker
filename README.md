# Exodus Sailing Tracker

Live map tracking dashboard designed for Garmin inReach integration, utilizing Windy.com Maps API and automated GitHub Actions to minimize hosting complexity.

## How it works

1. **Frontend App**: `index.html` loads data locally from `data.kml` and plots it over an interactive Windy weather map using Leaflet. 
2. **Data Automation**: A GitHub Action (`.github/workflows/update_data.yml`) is triggered externally by [cron-job.org](https://cron-job.org) on a reliable schedule to fetch the latest tracking feed from Garmin MapShare.
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

### Setting up GitHub Pages
To host this tracker online for free:
1. Go to your repository on GitHub and click **Settings** > **Pages**.
2. Under "Source", select **Deploy from a branch**.
3. Select your `main` branch and the `/ (root)` folder, then click **Save**.
4. GitHub will give you a public URL (e.g., `https://username.github.io/exodus-tracker/`) where your map is live.

### Setting up GitHub Actions (Auto-updater)
The workflow is triggered via `workflow_dispatch`, meaning it runs on demand rather than on a GitHub-managed cron.

1. Ensure your Garmin MapShare is enabled and the URL in `.github/workflows/update_data.yml` is correct.
2. Go to your repository **Settings** > **Actions** > **General**.
3. Scroll down to **Workflow permissions**, select **Read and write permissions**, and click **Save**.

### Scheduling with cron-job.org
GitHub's built-in cron scheduler is unreliable and can delay runs by hours under load. [cron-job.org](https://cron-job.org) provides a precise external trigger instead.

**1. Create a GitHub Personal Access Token (PAT)**
- Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
- Grant **Actions: Read and write** permission scoped to this repository only

**2. Create a cron job at cron-job.org**

| Field | Value |
|---|---|
| URL | `https://api.github.com/repos/amirlanesman/exodus-tracker/actions/workflows/update_data.yml/dispatches` |
| Method | `POST` |
| Schedule | Every 30 minutes (or your preferred interval) |

Add these **request headers**:
```
Authorization: Bearer YOUR_PAT_TOKEN_HERE
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Set the **request body** to:
```json
{"ref": "main"}
```

> A `204 No Content` response from GitHub means the trigger was accepted successfully.

