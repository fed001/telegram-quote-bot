# Wolfg

Wolfg is a Telegram Chatbot that is sending daily quotes to subscribers and lets you add your own quotes to its SQLite database. Quotes may be in any format, for example
- Text
- Pictures
- Voice / Video Notes


### Tech

Wolfg uses a number of open source Python libraries to work properly:

* [pyTelegramBotAPI] - Implementation for the Telegram Bot API
* [sqlalchemy] - SQL toolkit

### Installation

Wolfg requires [Python](https://www.python.org/) v2.7+ to run.

Install the dependencies, setup the database and start the chatbot.

```sh
$ cd wolfg
$ pip install -r requirements.txt
$ cd db
$ python setup_db.py
```

### Usage

```sh
$ export WOLFG_TELE_TOKEN=<TELEGRAM_BOT_TOKEN>
$ python -m tele.wolfg
```

   [pyTelegramBotAPI]: <https://github.com/eternnoir/pyTelegramBotAPI>
   [sqlalchemy]: <https://www.sqlalchemy.org>
   
