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


def get_data(url):
    reviews_url = url + "/tab/reviews"
    #img_url = url + "/tab/photos"
    #name = get_description_and_name(description_url)

    return {
        "reviews": get_reviews(reviews_url),
        #"description": desc,
        #"name": name,
        #"images": get_images(img_url)
    }

