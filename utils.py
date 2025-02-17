from datetime import datetime, timedelta

def generate_welcome_message():
    """
        Генерирует приветственное сообщение вида:
        "Рады приветствовать Вас в отеле Довиль! Сегодня <день недели>, <число> <месяц>.
         Температура воздуха от <temp_min>°C до <temp_max>°C, <описание погоды>."
        Описание погоды переводится с английского.
        """
    weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    now = datetime.now()
    weekday = weekdays[now.weekday()]
    day = now.day
    month = months[now.month]
    greeting = f"Рады приветствовать Вас в отеле Довиль! Сегодня {weekday}, {day} {month} 🌤️"

    # Получение информации о погоде
    try:
        from pyowm import OWM
        from pyowm_key import API_KEY
        owm = OWM(API_KEY)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place("Anapa, RU")
        w = observation.weather
        temp_data = w.temperature("celsius")
        temp_max = temp_data.get("temp_max")
        detailed_status = w.detailed_status  # Например, "clear sky"
        weather_map = {
            "clear sky": "ясно",
            "few clouds": "малооблачно",
            "scattered clouds": "рассеянные облака",
            "broken clouds": "облачно",
            "overcast clouds": "пасмурно",
            "shower rain": "ливень",
            "rain": "дождь",
            "thunderstorm": "гроза",
            "snow": "снег",
            "mist": "туман",
            "light snow": "небольшой снег",
        }
        status_ru = weather_map.get(detailed_status.lower(), detailed_status)
        if temp_max is not None:
            weather_info = f" Температура воздуха {temp_max:.0f}°C, {status_ru}. "
        else:
            weather_info = ""
    except Exception as e:
        weather_info = ""
    return greeting + weather_info