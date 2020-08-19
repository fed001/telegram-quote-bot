# telegram-quote-bot

telegram-quote-bot is a Telegram Chatbot that is sending daily quotes to subscribers and lets you add your own quotes to its Postgres database. Quotes may be in any format, for example
- Text
- Pictures
- Voice / Video Notes


### Libraries

telegram-quote-bot uses open source Python libraries:

* [pyTelegramBotAPI] - Implementation for the Telegram Bot API
* [sqlalchemy] - SQL toolkit

### Installation

telegram-quote-bot requires [Python](https://www.python.org/) v3.69+ to run.

Install the dependencies, setup the database, configure Telegram access in the .cfg and start the chatbot.

```sh
$ cd telegram-quote-bot
$ tox
$ python setup_db.py
edit telegram_quote_bot.cfg
```

### Usage

```sh
$ python telegram_quote_bot.pyz
```

   [pyTelegramBotAPI]: <https://github.com/eternnoir/pyTelegramBotAPI>
   [sqlalchemy]: <https://www.sqlalchemy.org>
   
