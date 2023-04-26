import openai
import telebot
import time
import os

openai.api_key = os.environ.get('AFINA_API_KEY')
bot = telebot.TeleBot(os.environ.get('TB_API_KEY'))
user_data = []
sleep_time = 30
last_message_time = int(time.time())-sleep_time


def send_message(bt, chat, message):
    try:
        bt.send_message(chat_id=chat, text=message)
        return True
    except Exception as be:
        print("Возникла ошибка бота \n" + str(be))
        return False


@bot.message_handler(func=lambda _: True)
def handle_message(message):
    global last_message_time
    global user_data
    if int(time.time()) - last_message_time < sleep_time:
        print(int(time.time()) - last_message_time)
        time.sleep(sleep_time-(int(time.time()) - last_message_time))
    cur_dialog = []
    last_message_time = int(time.time())
    for data in user_data:
        cur_dialog.append({"role": data["role"], "content": data["content"]})
    if len(cur_dialog) == 0:
        print("Новая беседа с", str(message.from_user.id), message.from_user.first_name)
        user_data.append({
            "ID": message.chat.id,
            "time": last_message_time,
            "role": "user",
            "content": message.from_user.first_name+": Привет, Афина!"
        })
        user_data.append({
            "ID": message.chat.id,
            "time": last_message_time,
            "role": "assistant",
            "content": "Здравствуйте, " + message.from_user.first_name
        })
    user_data.append({
        "ID": message.chat.id,
        "time": last_message_time,
        "role": "user",
        "content": message.from_user.first_name+": "+message.text
    })
    for data in user_data:
        if data["ID"] == message.chat.id:
            cur_dialog.append({"role": data["role"], "content": data["content"]})
    print(message.from_user.first_name, ":", message.text)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=cur_dialog,
        )
        print("Afina : " + response.choices[0].message.content)
        user_data.append({
            "ID": message.from_user.id,
            "time": last_message_time,
            "role": "assistant",
            "content": response.choices[0].message.content
        })
        print(response)
        while int(response.usage.total_tokens) > 3500:
            for data in user_data:
                if data["ID"] == message.chat.id:
                    user_data.remove(data)
                    print("Очистка сообщений т.к. буфер переполнен ")
                    break
                if int(data["time"]) < int(time.time()) - 3600:
                    user_data.remove(data)
                    print("Очистка устаревших сообщений")
                    break
        while not send_message(bot, message.chat.id, response.choices[0].message.content):
            time.sleep(sleep_time)
    except Exception as aie:
        while not send_message(bot, message.chat.id, "Возникла ошибка \n"+str(aie)):
            time.sleep(sleep_time)



if __name__ == '__main__':
    print(last_message_time)
    bot.polling()
