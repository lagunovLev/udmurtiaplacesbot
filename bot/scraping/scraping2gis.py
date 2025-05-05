from urllib.parse import unquote, urlparse
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
}


def get_reviews(response):
    soup = BeautifulSoup(response, 'html.parser')
    reviews = []

    for review in soup.find_all('a', class_='_1msln3t'):
        text = review.text

        reviews.append({
            'text': text,
        })

    return reviews


def get_rating(response):
    soup = BeautifulSoup(response, 'html.parser')
    return soup.find("div", class_="_1tam240").text


def get_ratings_number(response):
    soup = BeautifulSoup(response, 'html.parser')
    return soup.find("div", class_="_1y88ofn").text


def get_description_and_name(url):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    #desc = soup.find('div', class_="_spilqd").find('span').text
    name = soup.find("h1", class_="_1x89xo5").find("span").text

    return name


def get_images(url):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    style = soup.find('div', class_="_1dk5lq4")#["style"]
    print(style)
    #urls = re.findall(r'url\(&quot;(https?://[^&]+)&quot;\)', style)
    #return urls[-1]
    return None


def extract_2gis_coordinates(url: str) -> tuple[tuple[float, float], tuple[float, float] | None]:
    """
    Извлекает координаты из ссылки 2GIS.

    Возвращает:
        - Основные координаты (из пути URL)
        - Опциональные координаты из параметра `m` (если есть)

    Пример:
        >>> url = "https://2gis.ru/izhevsk/firm/123/53.215475%2C56.850349?m=53.215903%2C56.850599"
        >>> main_coords, m_coords = extract_2gis_coordinates(url)
        >>> print(main_coords)  # (53.215475, 56.850349)
        >>> print(m_coords)     # (53.215903, 56.850599)
    """
    decoded_url = unquote(url)

    # Извлекаем основные координаты (из пути)
    path_match = re.search(r'/(\d+\.\d+),(\d+\.\d+)(?:\?|$)', decoded_url)
    #if not path_match:
    #    raise ValueError(f"Не удалось извлечь координаты из URL {url}")

    main_coords = (0, 0)
    if path_match:
        lat1, lon1 = map(float, path_match.groups())
        main_coords = (lat1, lon1)

    # Извлекаем координаты из параметра `m` (если есть)
    query = urlparse(decoded_url).query
    m_match = re.search(r'm=([^/]+)', query)
    m_coords = (0, 0)

    if m_match:
        coords_str = m_match.group(1)
        lat2, lon2 = map(float, coords_str.split(',')[:2])
        m_coords = (lat2, lon2)

    return main_coords, m_coords


def get_data(url):
    reviews_url = url.split("?")[0] + "/tab/reviews" + "?" + url.split("?")[1] if "?" in url else url + "/tab/reviews"
    main_coords, m_coords = extract_2gis_coordinates(url)

    print("Извлекаем html")
    options = Options()
    options.headless = True
    print("Запуск драйвера")
    driver = webdriver.Chrome(options=options)
    print("==============")
    driver.get(reviews_url)
    print("Извлекаем html")
    reviews_response = driver.page_source
    driver.quit()
    print("Извлечен html")

    return {
        "latitude": main_coords[1] or m_coords[1],
        "longtitude": main_coords[0] or m_coords[0],
        "url": url,
        "reviews": get_reviews(reviews_response),
        "rating": get_rating(reviews_response),
        "ratings_number": get_ratings_number(reviews_response),
    }

