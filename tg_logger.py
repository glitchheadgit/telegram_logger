import os
import requests
import sys
import time
import json
import traceback
from io import StringIO


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class telegram_logger():
    def __init__(self, chat_id, name="wrapper") -> None:
        super().__init__()
        self.chat_id = os.getenv("TG_CHAT_ID")
        self.token = os.getenv("TG_API_TOKEN")
        self.url = f"https://api.telegram.org/bot{self.token}/"
        self.name = name

    def __call__(self, func):
        return telegram_logger_decorator(self.chat_id)(func)

    def __enter__(self):
        self.buffer = StringIO()
        sys.stdout = self.buffer
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        log_file = f"{self.name}.log"

        if elapsed_time < 86400:
            time_str = time.strftime(
                "%H:%M:%S.%f" if exc_type else "%H:%M:%S", time.gmtime(elapsed_time)
            )
        else:
            days = int(elapsed_time // 86400)
            time_str = time.strftime(
                f"{days} days, %H:%M:%S", time.gmtime(elapsed_time)
            )
        if exc_type:
            print(
                "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                file=self.buffer,
            )
            message = f"""&#128548; Wrapper encountered an error\nRuntime: <code>{time_str}</code>\n\n<code>{exc_type.__name__ + ' : ' + str(exc_value) if str(exc_value) else exc_type.__name__}</code>"""
        else:
            message = (
                f"&#x2728; Wrapper executed successfully in <code>{time_str}</code>"
            )
        self.buffer.seek(0)
        r = requests.post(
            self.url + "sendDocument",
            data={"chat_id": self.chat_id, "caption": message, "parse_mode": "html"},
            files={"document": (log_file, self.buffer)},
        )

        if r.status_code // 100 != 2:
            r = requests.post(
                self.url + "sendMessage",
                data={
                    "chat_id": self.chat_id,
                    "text": message + "\nWrapper doesn't have logs!",
                    "parse_mode": "html",
                },
            )
        self.buffer.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


def telegram_logger_decorator(chat_id):
    token = os.getenv("TG_API_TOKEN")
    url = f"https://api.telegram.org/bot{token}/"

    def decorator(func):
        def wrapper(*args, **kwargs):
            buffer = StringIO()
            sys.stdout = buffer
            sys.stderr = buffer
            start_time = time.time()
            func_name = func.__name__
            log_file = f"{func_name}.log"
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time < 86400:  # Время выполнения менее 1 дня
                    time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
                else:
                    days = int(elapsed_time // 86400)
                    time_str = time.strftime(
                        f"{days} days, %H:%M:%S", time.gmtime(elapsed_time)
                    )
                message = f"&#x2728; Function <code>{func_name}</code> executed successfully in <code>{time_str}</code>"
                buffer.seek(0)
                r = requests.post(
                    url + "sendDocument",
                    data={"chat_id": chat_id, "caption": message, "parse_mode": "html"},
                    files={"document": (log_file, buffer)},
                )
                if r.status_code // 100 != 2:
                    r = requests.post(
                        url + "sendMessage",
                        data={
                            "chat_id": chat_id,
                            "text": message + "\nFunction doesn't have logs!",
                            "parse_mode": "html",
                        },
                    )
                return result
            except Exception as e:
                end_time = time.time()
                elapsed_time = end_time - start_time

                if elapsed_time < 86400:
                    time_str = time.strftime("%H:%M:%S.%f", time.gmtime(elapsed_time))
                else:
                    days = int(elapsed_time // 86400)
                    time_str = time.strftime(
                        f"{days} days, %H:%M:%S", time.gmtime(elapsed_time)
                    )

                error_type = type(e).__name__
                error_text = str(e)
                error_message = f"&#128548; Function <code>{func_name}</code> encountered an error:\n\n<code>{error_type + ' : ' + error_text if error_text else error_type}</code>"
                buffer.seek(0)
                r = requests.post(
                    url + "sendDocument",
                    data={
                        "chat_id": chat_id,
                        "caption": error_message,
                        "parse_mode": "html",
                    },
                    files={"document": (log_file, buffer)},
                )
                if r.status_code // 100 != 2:
                    r = requests.post(
                        url + "sendMessage",
                        data={
                            "chat_id": chat_id,
                            "text": error_message + "\nFunction doesn't have logs!",
                            "parse_mode": "html",
                        },
                    )
                return result
            finally:
                buffer.close()

        return wrapper

    return decorator


def get_chatid():
    token = os.getenv("TG_API_TOKEN")
    url = f"https://api.telegram.org/bot{token}/"
    r = requests.get(url + "getUpdates")
    data = {}
    try:
        data = json.loads(r.text)
        return data["result"][-1]["message"]["from"]["id"]
    except Exception as e:
        print("Couldn't parse ID from Telegram API response:\n", data)