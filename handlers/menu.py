import aiohttp
from config import SPOONACULAR_API_KEY


async def get_meal_nutrition(meal_id: int) -> dict:
    """Получает КБЖУ для конкретного блюда по его ID."""
    url = f"https://api.spoonacular.com/recipes/{meal_id}/information"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeNutrition": "true"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                nutrition = data.get("nutrition", {}).get("nutrients", [])
                result = {
                    "calories": 0,
                    "protein": 0,
                    "fat": 0,
                    "carbohydrates": 0
                }
                for nutrient in nutrition:
                    name = nutrient["name"].lower()
                    amount = nutrient["amount"]
                    if name == "calories":
                        result["calories"] = round(amount)
                    elif name == "protein":
                        result["protein"] = round(amount, 1)
                    elif name == "fat":
                        result["fat"] = round(amount, 1)
                    elif name == "carbohydrates":
                        result["carbohydrates"] = round(amount, 1)
                return result
            else:
                return {"calories": 0, "protein": 0, "fat": 0, "carbohydrates": 0}


async def build_menu_text(user_data: dict) -> str:
    """
    Генерирует план питания на один день с КБЖУ для каждого приема пищи.

    Args:
        user_data (dict): Данные пользователя (goal, weight, height, age, gender, allergies, timeframe)

    Returns:
        str: Текстовый план питания на день
    """
    goal = user_data["goal"].lower()
    timeframe = user_data["timeframe"].lower()
    weight = user_data["weight"]
    height = user_data["height"]
    age = user_data["age"]
    gender = user_data["gender"].lower()
    allergies = user_data["allergies"] if user_data["allergies"] != "Нет" else ""

    # Рассчитываем базовый метаболизм (Mifflin-St Jeor)
    if gender == "мужской":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Учитываем цель и период
    if goal == "похудение":
        if "3 месяца" in timeframe:
            target_calories = int(bmr * 0.7)
        elif "полгода" in timeframe:
            target_calories = int(bmr * 0.8)
        elif "год" in timeframe:
            target_calories = int(bmr * 0.85)
        else:
            target_calories = int(bmr * 0.8)
    elif goal == "набор массы":
        if "3 месяца" in timeframe:
            target_calories = int(bmr * 1.25)
        elif "полгода" in timeframe:
            target_calories = int(bmr * 1.15)
        elif "год" in timeframe:
            target_calories = int(bmr * 1.1)
        else:
            target_calories = int(bmr * 1.15)
    else:
        target_calories = int(bmr)

    url = "https://api.spoonacular.com/mealplanner/generate"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "timeFrame": "day",
        "targetCalories": target_calories,
    }
    if allergies:
        params["excludeIngredients"] = allergies

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                meals = data.get("meals", [])
                nutrients = data.get("nutrients", {})

                menu = f"🍽 <b>План питания на день для {goal} (~{target_calories} ккал)</b>\n"
                menu += f"Период: {timeframe}\n\n"

                for i, meal in enumerate(meals, 1):
                    nutrition = await get_meal_nutrition(meal["id"])
                    menu += f"  <b>Прием {i}: {meal['title']}</b>\n"
                    menu += f"  Время приготовления: {meal['readyInMinutes']} мин\n"
                    menu += f"  Ссылка на рецепт: {meal['sourceUrl']}\n"
                    menu += f"  КБЖУ: {nutrition['calories']} ккал, "
                    menu += f"Б: {nutrition['protein']} г, Ж: {nutrition['fat']} г, У: {nutrition['carbohydrates']} г\n\n"

                menu += f"<b>Итого за день</b>:\n"
                menu += f"Калории: {nutrients.get('calories', 0)} ккал\n"
                menu += f"Белки: {nutrients.get('protein', 0)} г\n"
                menu += f"Жиры: {nutrients.get('fat', 0)} г\n"
                menu += f"Углеводы: {nutrients.get('carbohydrates', 0)} г"

                return menu
            else:
                return f"Ошибка при запросе к API: {response.status}. Попробуйте позже."