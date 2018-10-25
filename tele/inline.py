from os import environ
from telebot import types
from core import dbQuery
from core.constants import exclamation_mark_pic_url

if 'GAME_SERVER_IP' in locals():
    game_server_ip = environ['GAME_SERVER_IP']
else:
    game_server_ip = None


def inline_default_proc(bot, inline_query):
    bot.answer_inline_query(
        inline_query.id,
        [types.InlineQueryResultGame(id = '1', game_short_name = 'mygame')])


def inline_proc(bot, inline_query):
    results = get_inline_results('game', inline_query.query, inline_query.id)

    if results:
        bot.answer_inline_query(inline_query.id, results)
    else:
        results.append(types.InlineQueryResultArticle(
              id = int(inline_query.id),
              title = 'No Results.',
              input_message_content = types.InputTextMessageContent(message_text = 'Nothing found.'),
              thumb_url = exclamation_mark_pic_url))
        bot.answer_inline_query(inline_query.id, results)


def get_inline_results(column, string, start_index):
    results = []
    inline_query_rows = enumerate(dbQuery.query(
        """SELECT DISTINCT GAME FROM GAMES
           WHERE {0} LIKE ? LIMIT 3""".format(column), ('%' + string.encode('utf-8') + '%', )))

    for i, item in inline_query_rows:
        game = item[0]
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton(text = game, url = game_server_ip))
        results.append(types.InlineQueryResultGame(
            id = int(start_index) + i + 1,
            game_short_name = game))

    return results

