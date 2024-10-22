import random
import re

import psycopg2

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = ''
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


def table_of_common_words():
    words_start = [('hello', 'привет'), ('peace', 'мир'), ('red', 'красный'), ('green', 'зеленый'),
                   ('yellow', 'желтый'), ('blue', 'синий'), ('black', 'черный'), ('grey', 'серый'),
                   ('white', 'белый'), ('car', 'машина')
                   ]
    with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users(
                	id SERIAL PRIMARY KEY,
                	users_id_telegram INTEGER NOT NULL
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS words(
                    id SERIAL PRIMARY KEY,
                    word_en VARCHAR(25) NOT NULL,
                    word_ru VARCHAR(25) NOT NULL,
                    start_word BOOLEAN DEFAULT false
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_words(
                	users INTEGER REFERENCES users(id),
                	words INTEGER REFERENCES words(id),
                	CONSTRAINT uw PRIMARY KEY (users, words)
                );
            """)

            for word_en, word_ru in words_start:
                cur.execute("""
                    insert  into words(word_en, word_ru, start_word)
                    values(%s, %s, true);
                """, (word_en, word_ru,))


def next_words(user):
    with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
        with conn.cursor() as cur:  # ________________________________________________________________тут
            cur.execute("""
                SELECT id FROM users
                WHERE users_id_telegram=%s
            """, (user,))
            user_id = cur.fetchall()[0][0]

            cur.execute("""
                SELECT word_en, word_ru FROM words w
                LEFT JOIN user_words uw on w.id = uw.words
                WHERE users=%s ORDER BY random() LIMIT %s
            """, (user_id, 4,))
            words = cur.fetchall()
            target_word = words[0][0]
            translate = words[0][1]
            others = [words[1][0], words[2][0], words[3][0], ]
    return [target_word, translate, others]


def words_ru_en(words):
    ru = re.compile(r'([а-яё])')
    en = re.compile(r'([a-z])')
    word_ru = None
    word_en = None
    for n, word in enumerate(words.lower().split()):
        if n > 1:
            print('Введено больше двух слов')
            break
        if ru.search(word) and en.search(word):
            print('В слове присутствуют и русские и английские символы:', word)
            break
        elif ru.search(word):
            word_ru = word  # найдены руские символы
        elif en.search(word):
            word_en = word  # найдены английские символы
    return word_en, word_ru


def add_word_translation(massage):
    id = massage.from_user.id
    word_translation = words_ru_en(massage.text)
    if word_translation[0] and word_translation[1]:
        user_words_save = False
        with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT word_en, word_ru FROM words WHERE word_en=%s or word_ru=%s;
                """, (word_translation[0], word_translation[1]))
                select_words = cur.fetchall()
                if select_words == []:  # проверка на дабавку слова
                    cur.execute("""
                        insert  into words(word_en, word_ru)
                        values(%s, %s);
                    """, (word_translation[0], word_translation[1],))

                    cur.execute("""
                        SELECT id FROM words WHERE word_en=%s;
                    """, (word_translation[0],))
                    word_id = cur.fetchall()  # узнаем word_id

                    user_words_save = True
                else:  # такое слово в базе уже есть
                    cur.execute("""
                        SELECT id FROM words WHERE word_en=%s;
                    """, (word_translation[0],))
                    word_id = cur.fetchall()  # узнаем word_id

                    cur.execute("""
                         SELECT id FROM users WHERE users_id_telegram=%s;
                     """, (id,))
                    u_id = cur.fetchall()[0][0]  # узнаем user_id

                    cur.execute("""
                        SELECT id FROM words w
                        LEFT JOIN user_words uw on w.id = uw.words
                        WHERE w.id=%s and uw.users=%s;
                    """, (word_id[0][0], u_id))
                    if cur.fetchall() == []:
                        user_words_save = True

        if user_words_save == True:
            with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM users WHERE users_id_telegram=%s;
                    """, (id,))
                    u_id = cur.fetchall()[0][0]
            user_words(user_id=u_id, words_id=word_id)


def save_word_user_bd(user_id_telegram):
    user_words_ok = False
    with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS(SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'words')
            """)

            if cur.fetchall()[0][0] == False:
                table_of_common_words()  # добовляем в базу данных общие слова

            # создаем запись юзера тг
            cur.execute("""
                SELECT id FROM users WHERE users_id_telegram=%s;
            """, (user_id_telegram,))
            if cur.fetchall() == []:
                cur.execute("""
                    insert  into users(users_id_telegram)
                    values(%s);
                """, (user_id_telegram,))
                # добовляем общие слова userу
                # узнаем id usera
                cur.execute("""
                    SELECT id FROM users WHERE users_id_telegram=%s;
                """, (user_id_telegram,))
                user_id = cur.fetchall()[0][0]

                cur.execute("""
                    SELECT id FROM words w
                     WHERE start_word=true
                """)
                word_id = cur.fetchall()
                user_words_ok = True
    if user_words_ok:  # если нужно вносим слова в промежточную таблцу
        user_words(user_id=user_id, words_id=word_id)


def user_words(user_id, words_id):
    with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM users;
            """)
            for word_id in words_id:
                cur.execute("""
                    insert  into user_words(users, words)
                    values(%s, %s);
                """, (user_id, word_id,))


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        save_word_user_bd(
            user_id_telegram=message.from_user.id)  # если не добавленны общие слова добовляем, и устанавливаем связь общих слов с юзером
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    rand_words_bd = next_words(user=message.from_user.id)

    global buttons
    buttons = []
    target_word = rand_words_bd[0]  # брать из БД
    translate = rand_words_bd[1]  # брать из БД
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = rand_words_bd[2]  # брать из БД
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:

        with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM users
                    WHERE users_id_telegram=%s;
                """, (message.from_user.id,))
                id_user = cur.fetchall()[0][0]

                cur.execute("""
                    SELECT id FROM words
                    WHERE word_en=%s;
                """, (data['target_word'],))
                id_word = cur.fetchall()[0][0]

                # проверка на стартовое слово
                cur.execute("""
                    SELECT start_word FROM words w
                    LEFT JOIN user_words uw on w.id = uw.words
                    WHERE word_en=%s AND uw.users=%s
                """, (data['target_word'], id_user,))
                start_word = cur.fetchall()[0][0]

                cur.execute("""
                            DELETE FROM user_words WHERE users=%s AND words=%s
                        """, (id_user, id_word,))
                if start_word == False:  # проверка как добавлено слва пользователем или из общего списка
                    cur.execute("""
                        SELECT users, words FROM user_words
                        WHERE users!=%s and words=%s
                    """, (id_user, id_word))

                    if cur.fetchall() == []:  # у других пользователей нет этого слова
                        cur.execute("""
                            DELETE FROM words WHERE word_en=%s
                        """, (data['target_word'],))


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    print(message.text)  # сохранить в БД
    word_en = ''
    word = bot.send_message(cid, 'Введите слово и его перевод')
    bot.register_next_step_handler(word, add_word_translation)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
