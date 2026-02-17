# Telegram Cornice Calculator Bot (VS Code)

## Что нового
- Поддержка файла **.env** (можно не задавать переменную окружения вручную)
- Команда **/test** — прогоняет контрольные значения и печатает результаты

## Быстрый старт (VS Code)
1) Распакуйте архив и откройте папку в VS Code.
2) Terminal -> New Terminal.

### Виртуальное окружение
**Windows (PowerShell):**
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS/Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Токен
### Вариант A (рекомендуется): .env
1) Скопируйте `.env.example` в `.env`
2) Вставьте ваш токен:
```
BOT_TOKEN=123456:ABCDEF...
```

### Вариант B: переменная окружения
**Windows (PowerShell):**
```
$env:BOT_TOKEN="ВАШ_ТОКЕН"
```
**macOS/Linux:**
```
export BOT_TOKEN="ВАШ_ТОКЕН"
```

## Запуск
```
python bot.py
```

## Проверка
- В Telegram откройте бота, отправьте `/start`
- Для самопроверки: отправьте `/test`

## Логика (как калькулятор)
- К центру: L = X - 15.2
- Слева-Направо: L = X - 11.6
- Схема: N = ceil(L/300), S = round(L/N, 1) -> S выводится N раз
- Бегунки: even_up(ceil(X/8))
- Крючки: бегунки + 10
- Крепления: ceil(X/100) + 1
