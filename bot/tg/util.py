from cleantext import clean


def compare_input(input_str: str, phrase: str):
    input_str = clean(input_str, lower=True, no_emoji=True)
    phrase = clean(phrase, lower=True, no_emoji=True)
    return input_str == phrase


def rating_to_stars(rating_str):
    try:
        # Преобразуем строку в число и округляем
        rating = round(float(rating_str))

        # Ограничиваем оценку диапазоном 1-5
        rating = max(1, min(5, rating))

        # Создаем строку со звездами
        filled_star = '⭐'
        empty_star = '☆'
        stars = filled_star * rating + empty_star * (5 - rating)

        return stars
    except (ValueError, TypeError):
        # В случае ошибки возвращаем 0 звезд (можно изменить на другое поведение)
        return '☆☆☆☆☆'
