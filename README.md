# TG Video Bot

A Telegram bot for downloading supported video links and sending them to Telegram chat or posting to a Telegram channel.

This project is designed to run on **Termux** or Linux with Python, `yt-dlp`, and `ffmpeg`.

## Features

- Accepts a video URL in Telegram.
- Fetches video info with `/info`.
- Downloads supported video links with `/dl`.
- Posts downloaded video to your Telegram channel with `/post`.
- Supports a local `cookies.txt` file for logged-in access on some supported sites.
- Built for local/self-hosted use with GitHub + Termux workflow.

## Important notes

- This project is intended only for content you are authorized to access and store.
- A cookies file may help with logged-in access on some supported sites, but it does **not** guarantee support for every site.
- Some embedded players, signed URLs, DRM-protected streams, or unsupported platforms will not work.
- Do **not** upload `.env`, `cookies.txt`, or other secrets to GitHub.

## Project structure

```text
tgvideo-bot/
├── bot.py
├── downloader.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── downloads/
├── logs/
└── secrets/
    └── cookies.txt
```

## Requirements

- Termux or Linux
- Python 3
- Git
- ffmpeg
- A Telegram bot token from BotFather
- Your Telegram numeric user ID
- Optional: a Telegram channel username where the bot is admin
- Optional: `cookies.txt` exported from a browser session for a supported site

## Termux setup

Run these commands in Termux:

```bash
termux-setup-storage
pkg update && pkg upgrade
pkg install git python ffmpeg
```

Clone your repo:

```bash
git clone https://github.com/ayaz50sm/tgvideo-bot.git
cd tgvideo-bot
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install Python dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Create local folders:

```bash
mkdir -p secrets downloads logs
```

Create your `.env` file from the example:

```bash
cp .env.example .env
nano .env
```

## .env configuration

Put your real values into `.env`:

```env
BOT_TOKEN=put_your_bot_token_here
ADMIN_USER_ID=123456789
CHANNEL_ID=@your_channel_username
COOKIE_FILE=./secrets/cookies.txt
DOWNLOAD_DIR=./downloads
MAX_FILE_SIZE_MB=1900
```

### Field explanation

- `BOT_TOKEN`: Your Telegram bot token from BotFather.
- `ADMIN_USER_ID`: Only this Telegram user ID can use the bot.
- `CHANNEL_ID`: Your channel username, for example `@mychannel`.
- `COOKIE_FILE`: Path to your exported cookies file.
- `DOWNLOAD_DIR`: Local folder where videos will be saved.
- `MAX_FILE_SIZE_MB`: Local bot-side size check before upload.

## Cookie file

If you need logged-in access for a supported site, place your exported browser cookies file here:

```text
./secrets/cookies.txt
```

### Cookie tips

- Keep it local only.
- Never commit it to GitHub.
- Export it in a compatible `cookies.txt` format.
- Replace it when the login session expires.
- One cookies file may contain cookies for multiple sites.

## Run the bot

Start the bot:

```bash
python bot.py
```

If everything is correct, the bot will start polling for messages.

## Telegram commands

- `/start` — show command help
- `/info <url>` — fetch basic video info
- `/dl <url>` — download and send the video to your Telegram chat
- `/post <url>` — download and post the video to your channel

You can also send a plain URL message to the bot, and it will try to download it.

## How to use

### 1. Start the bot
Message your bot on Telegram:

```text
/start
```

### 2. Check video info
```text
/info https://example.com/video
```

### 3. Download to chat
```text
/dl https://example.com/video
```

### 4. Post to channel
```text
/post https://example.com/video
```

For channel posting, make sure your bot is an admin in the target channel.

## GitHub safety

Keep these files out of Git:

- `.env`
- `secrets/cookies.txt`
- downloaded videos
- logs
- session files

That is why the repository includes a `.gitignore` file.

## Updating the bot

When you change code in GitHub, update it in Termux with:

```bash
cd tgvideo-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Troubleshooting

### Bot does not start
Check:
- `BOT_TOKEN` is correct
- Python packages are installed
- virtual environment is activated

### URL is not downloading
Possible reasons:
- Site is not supported by `yt-dlp`
- Login is required and cookies are missing
- Cookies expired
- Source uses signed URLs, token-based access, or other restrictions
- The source is not a direct media link

### Video downloads but Telegram upload fails
Check:
- file size
- channel permissions
- internet connection
- bot admin rights in the channel

### ffmpeg error
Make sure `ffmpeg` is installed:

```bash
ffmpeg -version
```

## License

This project uses the MIT License. See the `LICENSE` file for details.

## Disclaimer

Use this project only for content you have permission to access, store, or repost. Site support depends on the source, extractor support, and login/session behavior.
