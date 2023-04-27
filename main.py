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
last_message_time = int(time.time())-sleep_time
# список имен, на которые отликается афина
list_of_names = ['afina', 'athena', 'афина']
# срок жизни сообщений в памяти афины
max_message_live = 3600
# максимальная длина диалога в токенах
max_dialog_tokens = 4097


# отправка сообщения в telegram
def send_message(bt, chat, message):
    try:
        # вернуть True, если ошибок не возникло
        bt.send_message(chat_id=chat, text=message)
        return True
    except Exception as be:
        # вернуть False и зарегистрировать ошибку, если она возникла
        print("Возникла ошибка бота \n" + str(be))
        return False
def create_dialog(curdialog, userdata, chat_id):
    # формирование истории для запроса к gpt c очисткой диалога от старых сообщений, старше определенного времени жизни
    for data in userdata:
        if data["ID"] == chat_id:
            if int(data["time"]) < int(time.time()) - max_message_live:
                userdata.remove(data)
                print("Очистка устаревших сообщений")
            else:
                curdialog.append({"role": data["role"], "content": data["content"]})


# обработка сообщения поступившего боту
@bot.message_handler(func=lambda _: True)
def handle_message(message):
    global last_message_time
    global user_data
    # определение времени прошедшего с момента отправки предыдущего сообщения
    if int(time.time()) - last_message_time < sleep_time:
        print("Ждем -",sleep_time-(int(time.time()) - last_message_time), "сек")
        # сделать необходимую паузу
        time.sleep(sleep_time-(int(time.time()) - last_message_time))
    # обнулить список сообщений
    cur_dialog = []
    # зафиксировать время текущего сообщения
    last_message_time = int(time.time())
    # проверить набор сообщений на наличие ткущего чата
    for data in user_data:
        if data["ID"] == message.chat.id:
            cur_dialog.append({"role": data["role"], "content": data["content"]})
            break
    # если текущий чат пуст, познакомить пользователя
    if len(cur_dialog) == 0:
        print("Новая беседа с", str(message.from_user.id), message.from_user.first_name)
        user_data.append({"ID": message.chat.id,"time": last_message_time,
            "role": "user","content": message.from_user.first_name+": Привет, Афина!"})
        user_data.append({"ID": message.chat.id,"time": last_message_time,
            "role": "assistant","content": "Здравствуйте, " + message.from_user.first_name})
    # добавить в чаты текущее сообщение пользователя
    user_data.append({"ID": message.chat.id,"time": last_message_time,
        "role": "user","content": message.from_user.first_name+": "+message.text})
    print(message.from_user.first_name, ":", message.text)
    # определение обращения к Афине
    for name in list_of_names:
        # если присутсвует имя афина или чат приватный, то
        if (name.lower() in message.text.lower()) or (message.chat.type == 'private'):
            # сформировать диалог
            get_response = False
            # делаем попытки запросов пока ответ не влезет в рамки максимального значение токенов
            while not get_response:
                cur_dialog = []
                create_dialog(cur_dialog, user_data, message.chat.id)
                try:
                    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=cur_dialog)
                    print("Afina : " + response.choices[0].message.content)
                    print("Использовано токенов -", response.usage.total_tokens)
                    if int(response.usage.total_tokens) < max_dialog_tokens:
                        get_response = True
                        # запоминаем ответ
                        user_data.append({"ID": message.from_user.id,"time": last_message_time,
                        "role": "assistant","content": response.choices[0].message.content})
                        # попытка отправить ответа в чат

                        while not send_message(bot, message.chat.id, response.choices[0].message.content):
                            print("Ждем -", sleep_time, "сек")
                            time.sleep(sleep_time)
                    else:
                        del_mes=0
                        for data in user_data:
                            if data["ID"] == message.chat.id:
                                print("Очистка старых сообщений, буфер переполнен ", data["content"])
                                user_data.remove(data)
                                del_mes +=1
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
