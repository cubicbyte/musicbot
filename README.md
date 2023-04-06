# 1. Настройка

Для начала нужно настроить бота через файл `.env`:

1. Переименуйте файл `.env.example` в `.env`
2. Заполните необходимые поля в файле `.env`

# 2. Установка

## По-хорошему нужно использовать виртуальное окружение:
```bash
# Если не установлен venv
pip3 install -U --user virtualenv

# Создание виртуального окружения
python -m venv ./venv
```

Активация виртуального окружения

```bash
# Windows
.\venv\Scripts\activate

# Linux
source ./venv/bin/activate
```

## Установка зависимостей
```bash
pip install -r requirements.txt
```

# 3. Запуск
С виртуальным окружением:
```bash
# Windows
.\venv\Scripts\activate | python run.py

# Linux
source venv/bin/activate && python run.py
```

Без виртуального окружения:
```bash
python3 run.py
```

> **Warning** Если вы не используете venv, то вам необходимо добавить папку "**[python_dir]\Scripts**" в **PATH**
