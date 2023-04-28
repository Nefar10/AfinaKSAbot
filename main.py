import openai
import telebot
import time
import os

# ваш openai API key
openai.api_key = os.environ.get('AFINA_API_KEY')
# ваш telegram bot API key
bot = telebot.TeleBot(os.environ.get('TB_API_KEY'))
# текущая база диалогов
user_data = []
# время задержки в работе бота
sleep_time = 30
# время последнего сообщения
last_message_time = int(time.time()) - sleep_time
# список имен, на которые отликается афина
list_of_names = ['Afina', 'Athena', 'Афина']
# срок жизни сообщений в памяти афины
max_message_live = 3600
# максимальная длина диалога в токенах
max_dialog_tokens = 4097
# статус бота для каждого чата
bot_chat_states = []


def save_to_log(mess_time, user_name, chat_id, message):
    try:
        with open('msg\\chat' + str(chat_id) + '.txt', 'a', encoding='utf-8') as f:
            f.write('\n' + str(mess_time) + " " + user_name + " : " + message)
        return True
    except:
        return False


def err_log(err_text):
    try:
        with open('log\\errors.log', 'a', encoding='utf-8') as f:
            f.write('\n' + err_text)
        return True
    except:
        return False


# отправка сообщения в telegram
def send_message(bt, chat_id, message):
    try:
        # вернуть True, если ошибок не возникло
        bt.send_message(chat_id=chat_id, text=message)
        return True
    except Exception as be:
        # вернуть False и зарегистрировать ошибку, если она возникла
        print("Возникла ошибка бота \n" + str(be))
        return False
    finally:
        if not save_to_log(last_message_time, "Afina", chat_id, message):
            err_log(str(int(time.time())))


def create_dialog(userdata, mess):
    curdialog = []
    need_hello = True
    for data in userdata:
        if data["ID"] == mess.chat.id:
            if ": Привет," in data["content"]:
                need_hello = False
            if int(data["time"]) < int(time.time()) - max_message_live:
                userdata.remove(data)
                print("Очистка устаревших сообщений", data["content"])
            else:
                curdialog.append({"role": data["role"], "content": data["content"]})
    # если текущий чат пуст, познакомить пользователя
    if need_hello:
        print("Новая беседа с", str(mess.from_user.id), mess.from_user.first_name)
        userdata.insert(0, {"ID": mess.chat.id, "time": last_message_time,
                            "role": "assistant", "content": "Здравствуйте, " + mess.from_user.first_name})
        userdata.insert(0, {"ID": mess.chat.id, "time": last_message_time,
                            "role": "user",
                            "content": mess.from_user.first_name + ": Привет, " + list_of_names[0] + "!"})
        curdialog.insert(0, {"role": userdata[1]["role"], "content": userdata[1]["content"]})
        curdialog.insert(0, {"role": userdata[0]["role"], "content": userdata[0]["content"]})

    # формирование истории для запроса к gpt c очисткой диалога от старых сообщений, старше определенного времени жизни
    return curdialog


@bot.message_handler(commands=['chatlist'])
def send_chatlist(message):
    global bot_chat_states
    while not send_message(bot, message.chat.id, str(bot_chat_states)):
        print("Ждем -", sleep_time, "сек")
        time.sleep(sleep_time)


@bot.message_handler(commands=['send'])
def send_tochat(message):
    command, chat_id, text = message.text.split('\\')
    print("-", chat_id, text)
    while not send_message(bot, chat_id, text):
        print("Ждем -", sleep_time, "сек")
        time.sleep(sleep_time)


def get_chat_state(message):
    global bot_chat_states
    for chat in bot_chat_states:
        if chat["ID"] == message.chat.id:
            return chat["state"]
    bot_chat_states.append(({"ID": message.chat.id, "state": 'run', "Name": message.from_user.username}))
    return 'run'


def set_chat_state(chat_id, state):
    global bot_chat_states
    name = "None"
    for chat in bot_chat_states:
        if chat["ID"] == chat_id:
            name = chat["Name"]
            bot_chat_states.remove(chat)
            break
    bot_chat_states.append({"ID": chat_id, "state": state, "Name": name})
    print(bot_chat_states)


@bot.message_handler(commands=['state'])
def send_state(message):
    global bot_chat_states
    if get_chat_state(message) == 'run':
        while not send_message(bot, message.chat.id, "Я тут и все слышу!"):
            print("Ждем -", sleep_time, "сек")
            time.sleep(sleep_time)
    if get_chat_state(message) == 'sleep':
        while not send_message(bot, message.chat.id, "..."):
            print("Ждем -", sleep_time, "сек")
            time.sleep(sleep_time)


@bot.message_handler(commands=['wakeup'])
def send_welcome(message):
    global bot_chat_states
    if get_chat_state(message) == 'sleep':
        set_chat_state(message.chat.id, 'run')
        while not send_message(bot, message.chat.id, "Вжух!"):
            print("Ждем -", sleep_time, "сек")
            time.sleep(sleep_time)


@bot.message_handler(commands=['sleep'])
def send_sleep(message):
    global bot_chat_states
    if get_chat_state(message) == 'run':
        set_chat_state(message.chat.id, 'sleep')
        while not send_message(bot, message.chat.id, "Пока-пока..."):
            print("Ждем -", sleep_time, "сек")
            time.sleep(sleep_time)


# обработка сообщения поступившего боту
@bot.message_handler(func=lambda _: True)
def handle_message(message):
    global last_message_time
    global user_data
    global bot_chat_states
    # определение времени прошедшего с момента отправки предыдущего сообщения
    if int(time.time()) - last_message_time < sleep_time:
        print("Ждем -", sleep_time - (int(time.time()) - last_message_time), "сек")
        # сделать необходимую паузу
        time.sleep(sleep_time - (int(time.time()) - last_message_time))
    # зафиксировать время текущего сообщения
    last_message_time = message.date
    # добавить в чаты текущее сообщение пользователя
    user_data.append({"ID": message.chat.id, "time": last_message_time,
                      "role": "user", "content": message.from_user.first_name + ": " + message.text})
    save_to_log(last_message_time, message.from_user.first_name, message.chat.id, message.text)
    print(message.from_user.first_name, ":", message.text)
    # определение обращения к Афине
    for name in list_of_names:
        # если присутсвует имя афина или чат приватный, то формируем обращение
        if (get_chat_state(message) == 'run') and (
                (name.lower() in message.text.lower()) or (message.chat.type == 'private')):
            # сформировать диалог
            get_response = False
            # делаем попытки запросов пока ответ не влезет в рамки максимального значение токенов
            while not get_response:
                cur_dialog = create_dialog(user_data, message)
                print(cur_dialog)
                try:
                    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=cur_dialog)
                    print(list_of_names[0] + " : " + response.choices[0].message.content)
                    print("Использовано токенов -", response.usage.total_tokens)
                    if int(response.usage.total_tokens) < max_dialog_tokens:
                        get_response = True
                        # запоминаем ответ
                        user_data.append({"ID": message.from_user.id, "time": last_message_time,
                                          "role": "assistant", "content": response.choices[0].message.content})
                        # попытка отправить ответ в чат
                        while not send_message(bot, message.chat.id, response.choices[0].message.content):
                            print("Ждем -", sleep_time, "сек")
                            time.sleep(sleep_time)
                    else:
                        del_mes = 0
                        for data in user_data:
                            if data["ID"] == message.chat.id:
                                print("Очистка старых сообщений, буфер переполнен ", data["content"])
                                user_data.remove(data)
                                del_mes += 1
                                if del_mes == 4:
                                    break
                        print("Ждем -", sleep_time, "сек")
                        time.sleep(sleep_time)
                except openai.error.InvalidRequestError as aie:
                    # попытаться отправить сообщение о другой ошибке чата
                    while not send_message(bot, message.chat.id, "Возникла ошибка \n" + str(aie)):
                        print("Ждем -", sleep_time, "сек")
                        time.sleep(sleep_time)
            break


if __name__ == '__main__':
    print("Афина на связи!")
    bot.polling()
