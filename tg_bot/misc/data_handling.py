import json
import logging
from typing import Dict

all_records, reminder, black_list, appeals = {}, {}, {}, {"last_id": 0}
questions: Dict[str, list] = {}
categories, subcategories = [], {}

online_consultation = "Онлайн консультация"
office_consultation = "Консультация в офисе"
weekend = "Выходной"

services = {"online_consultation": online_consultation, "office_consultation": office_consultation}
timeline = {"9:00": {}, "10:00": {}, "11:00": {}, "12:00": {}, "13:00": {}, "14:00": {}, "15:00": {}, "16:00": {},
            "17:00": {}, "18:00": {}}

amount_time_per_service = {online_consultation: "01:00", office_consultation: "01:00", weekend: "01:00"}
service_prices = {online_consultation: 800, office_consultation: 1000}
bot_commands = {
    "/start": "Старт",
    "/filling": "Записаться на консультацию",
    "/records": "Ваши записи",
    "/appeals": "Обращения",
    "/common_questions": "Частые вопросы",
    "/contacts": "Контакты",
    "/apanel": "Меню администратора"
}

msg_to_delete = {"all": [], "fill": []}

logger = logging.getLogger(__name__)


async def upload_data():
    with open("tg_bot/misc/data/all_records.json", "w", encoding="utf-8-sig") as file:
        json.dump(all_records, file, indent=4, ensure_ascii=False)

    with open("tg_bot/misc/data/timeline.json", "w", encoding="utf-8-sig") as file:
        json.dump(timeline, file, indent=4, ensure_ascii=False)

    with open("tg_bot/misc/data/reminder.json", "w", encoding="utf-8-sig") as file:
        json.dump(reminder, file, indent=4, ensure_ascii=False)

    with open("tg_bot/misc/data/black_list.json", "w", encoding="utf-8-sig") as file:
        json.dump(black_list, file, indent=4, ensure_ascii=False)

    with open("tg_bot/misc/data/questions.json", "w", encoding="utf-8-sig") as file:
        json.dump(questions, file, indent=4, ensure_ascii=False)

    with open("tg_bot/misc/data/appeals.json", "w", encoding="utf-8-sig") as file:
        json.dump(appeals, file, indent=4, ensure_ascii=False)

    logger.info("Data has been successfully uploaded!")


async def load_data():
    try:
        with open("tg_bot/misc/data/all_records.json", encoding="utf-8-sig") as file:
            all_records.update(json.load(file))

        with open("tg_bot/misc/data/timeline.json", "r", encoding="utf-8-sig") as file:
            timeline.update(json.load(file))

        with open("tg_bot/misc/data/reminder.json", "r", encoding="utf-8-sig") as file:
            reminder.update(json.load(file))

        with open("tg_bot/misc/data/black_list.json", "r", encoding="utf-8-sig") as file:
            black_list.update(json.load(file))

        with open("tg_bot/misc/data/questions.json", "r", encoding="utf-8-sig") as file:
            questions.update(json.load(file))

        with open("tg_bot/misc/data/appeals.json", "r", encoding="utf-8-sig") as file:
            appeals.update(json.load(file))

            categories.extend([category for category in questions])
            for category in categories:
                subcategories.update({category: [subcategory for subcategory in questions[category]]})
    except FileNotFoundError:
        pass

    logger.info("Data has been successfully loaded!")
