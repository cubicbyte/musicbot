# 1. Настройка

Для начала нужно настроить бота через файл `config-example.py`:

1. Переименуйте файл `config-example.py` в `config.py`
2. Заполните необходимые поля в файле `config.py`

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
.\venv\Scripts\activate | python main.py

# Linux
source venv/bin/activate && python main.py
```

Без виртуального окружения:
```bash
python3 main.py
```
