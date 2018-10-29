from telebot import types
from core.constants import exclamation_mark_pic_url, sql_session, games


def inline_default_proc(bot, inline_query):
    bot.answer_inline_query(
        inline_query.id,
        [types.InlineQueryResultGame(id = '1', game_short_name = 'mygame')])


def inline_proc(bot, inline_query, game_server_ip):
    results = get_inline_results(inline_query.query, inline_query.id, game_server_ip)

    if results:
        bot.answer_inline_query(inline_query.id, results)
    else:
        results.append(types.InlineQueryResultArticle(
              id = int(inline_query.id),
              title = 'No Results.',
              input_message_content = types.InputTextMessageContent(message_text = 'Nothing found.'),
              thumb_url = exclamation_mark_pic_url))
        bot.answer_inline_query(inline_query.id, results)


def get_inline_results(string, start_index, game_server_ip):
    results = []
    inline_query_rows = sql_session.query(games.c.GAME_SHORT_NAME).filter(
        games.c.GAME_NAME.like('%' + string.encode('utf-8') + '%')).limit(3).all()
    i = 0
    for item in inline_query_rows:
        game = item[0]
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton(text = game, url = game_server_ip))
        results.append(types.InlineQueryResultGame(
            id = int(start_index) + i + 1,
            game_short_name = game))
        i += 1
    else:
        results.append([types.InlineQueryResultArticle(id = '1', title = 'No results.', input_message_content = 'k')])

    return results

