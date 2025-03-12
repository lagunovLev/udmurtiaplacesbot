from cleantext import clean


def compare_input(input_str: str, phrase: str):
    input_str = clean(input_str, lower=True, no_emoji=True)
    phrase = clean(phrase, lower=True, no_emoji=True)
    return input_str == phrase
