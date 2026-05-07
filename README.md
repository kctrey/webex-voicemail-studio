# Webex Voicemail Studio

A lightweight web application that allows end-users to record custom voicemail greetings directly from their browser, automatically appends a mandatory legal disclaimer (`disclaimer.mp3`), transcodes the audio to Webex Calling standards (8000Hz, Mono, u-Law), and securely uploads it to Webex.

## Features
- **In-Browser Recording**: Modern, glass-morphism UI for recording audio directly from the microphone.
- **Automated Processing**: Automatically appends a required disclaimer to all user recordings.
- **Webex Native**: Authenticates via Webex OAuth and uploads directly to the user's Voicemail configuration.
- **Proxy Friendly**: Fully supports hosting behind a reverse proxy sub-path (e.g., `/vm-studio/`).
- **Audit Logging**: Keeps an optional local log of which users uploaded greetings.

## Prerequisites

Before running this application, you must install the following system dependencies:

1. **Python 3.11 or higher**
   > *Note on Python versions*: The `wxc_sdk` dependency uses features (`typing.Self`) introduced in Python 3.11. If you attempt to run this on Python 3.10 or lower, you will encounter `ImportError` exceptions.

2. **FFmpeg** ⚠️ **CRITICAL REQUIREMENT** ⚠️
   This application relies heavily on `ffmpeg` to concatenate and transcode the audio files. **FFmpeg is NOT installed automatically via Python packages.** You must install it manually on your server and ensure it is available in your system's PATH.
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **RHEL/CentOS**: `sudo yum install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install ffmpeg`

## Installation

1. Clone the repository to your server:
   ```bash
   git clone <your-repository-url>
   cd webex-voicemail-studio
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Provide a disclaimer audio file:
   Ensure you have a file named `disclaimer.mp3` in the root directory of the project. If one is not present, a dummy 2-second silent file will be generated for testing.

## Configuration

1. Copy the example configuration file:
   ```bash
   cp config.example.json config.json
   ```

2. Create a Webex Integration:
   - Go to [developer.webex.com](https://developer.webex.com) and create a new **Integration**.
   - Add the following scopes:
     - `spark:kms`
     - `spark:people_read`
     - `spark:people_write`
     - `spark:telephony_config_read`
     - `spark:telephony_config_write`
   - Set the Redirect URI to match where you will host the app (e.g., `https://alerts.kctrey.net/vm-studio/oauth/callback`).

3. Edit `config.json` with your credentials:
   ```json
   {
       "webex": {
           "client_id": "YOUR_WEBEX_CLIENT_ID",
           "client_secret": "YOUR_WEBEX_CLIENT_SECRET",
           "redirect_uri": "https://yourdomain.com/vm-studio/oauth/callback",
           "static_token": "YOUR_STATIC_TEST_TOKEN"
       },
       "app": {
           "retain_wav_files": false,
           "enable_file_logging": false,
           "enable_audit_logging": true
       }
   }
   ```
   - **`retain_wav_files`**: If true, keeps the temporary user recordings instead of deleting them.
   - **`enable_file_logging`**: If true, logs Python stack traces to `app.log`.
   - **`enable_audit_logging`**: If true, writes a timestamp and the user's email to `audit.log` upon every successful upload.

## Running the Application

Run the server using Uvicorn:
```bash
python main.py
```
Or directly via uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Hosting Behind a Reverse Proxy
If you are deploying this behind a reverse proxy (like Nginx) on a specific sub-path (e.g., `/vm-studio`), **you must access the application using a trailing slash** in your browser (`/vm-studio/`). If the trailing slash is omitted, relative CSS and JS assets will fail to load.
