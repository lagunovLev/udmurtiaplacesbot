from urllib.parse import unquote, urlparse
import re
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
}


def get_reviews(url):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    reviews = []

    for review in soup.find_all('a', class_='_1msln3t'):
        #print(review)
        text = review.text

        reviews.append({
            'text': text,
        })

    return reviews


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
    if not path_match:
        raise ValueError("Не удалось извлечь координаты из URL")

    lat1, lon1 = map(float, path_match.groups())
    main_coords = (lat1, lon1)

    # Извлекаем координаты из параметра `m` (если есть)
    query = urlparse(decoded_url).query
    m_match = re.search(r'm=([^/]+)', query)
    m_coords = None

    if m_match:
        coords_str = m_match.group(1)
        lat2, lon2 = map(float, coords_str.split(',')[:2])
        m_coords = (lat2, lon2)

    return main_coords, m_coords


def get_data(url):
    reviews_url = url + "/tab/reviews"
    main_coords, m_coords = extract_2gis_coordinates(url)
    #img_url = url + "/tab/photos"
    #name = get_description_and_name(description_url)

    return {
        "reviews": get_reviews(reviews_url),
        "latitude": main_coords[1],
        "longtitude": main_coords[0],
        #"description": desc,
        #"name": name,
        #"images": get_images(img_url)
    }

