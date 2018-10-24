WOLFG
Telegram Bot

Installation:
1. Clone repository
2. Create virtualenv and activate
3. pip install -r requirements.txt
4. cd db && python setup_db.py

Run without Spotify:
1. export WOLFG_TELE_TOKEN=<TELEGRAM_BOT_TOKEN>
2. python -m TELE.wolfg

Run with Spotify:
1. export WOLFG_TELE_TOKEN=<TELEGRAM_BOT_TOKEN>
2. export SPOTIPY_CLIENT_SECRET==<SPOTIFY_SECRET>
3. export SPOTIPY_CLIENT_ID=<SPOTIFY_ID>
4. in section spotify of wolfg.cfg, replace user_id
5. python -m TELE.wolfg --spotify
