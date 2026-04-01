#!/data/data/com.termux/files/usr/bin/bash
cd ~/tgvideo-bot || exit 1
source venv/bin/activate
git pull
pip install -r requirements.txt
echo "Update done."
python bot.py
