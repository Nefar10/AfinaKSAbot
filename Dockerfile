FROM python:3.10-slim-buster

# Устанавливаем git для клонирования репозитория
RUN apt-get update && apt-get install -y git

# Клонируем репозиторий
RUN git clone https://github.com/Nefar10/AfinaKSAbot.git

# Устанавливаем зависимости
RUN pip install -r ./AfinaKSAbot/requirements.txt

# Указываем команду для запуска при старте контейнера
CMD ["python", "./AfinaKSAbot/main.py"]