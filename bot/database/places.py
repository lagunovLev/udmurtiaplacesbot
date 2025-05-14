from typing import List, Dict

from bson.objectid import ObjectId
import env_variables
from database import db_client
from pymongo import collection
from database import categories

collect: collection = db_client[env_variables.db_name]["places"]


def add(name, photos_id, description, category_name, reviews=None, lat=None, long=None, rating=None, ratings_number=None, url=None):
    collect.insert_one({"name": name,
                        "location": {"type": "Point", "coordinates": [long, lat]},
                        "rating": rating,
                        "ratings_number": ratings_number,
                        "url": url,
                        "photos_id": photos_id,
                        "description": description,
                        "category_id": categories.find_by_name(category_name)["_id"],
                        "likes_users_id": [],
                        "dislikes_users_id": [],
                        "reviews": reviews,
                        "likes": 0,
                        "dislikes": 0})


def update(place_id, name, photos_id, description, category_name, reviews=None, lat=None, long=None, rating=None, ratings_number=None, url=None):
    collect.update_one({"_id": ObjectId(place_id)},
                       {"$set": {"reviews": reviews,
                                 "location": {"type": "Point", "coordinates": [long, lat]},
                                 "rating": rating,
                                 "ratings_number": ratings_number,
                                 "url": url,
                                 "name": name,
                                 "photos_id": photos_id,
                                 "description": description,
                                 "category_id": categories.find_by_name(category_name)["_id"]
                                 }})


def get_nearest_places(
    user_lat: float,
    user_lng: float,
    max_distance: float = None,
    limit: int = None
) -> List[Dict]:
    """
    Возвращает точки из MongoDB, отсортированные по расстоянию от заданной координаты.

    Параметры:
        db_host (str): URI подключения к MongoDB (например, "mongodb://localhost:27017").
        db_name (str): Имя базы данных.
        collection_name (str): Имя коллекции с точками.
        user_lat (float): Широта пользователя.
        user_lng (float): Долгота пользователя.
        max_distance (float, опционально): Максимальное расстояние в метрах.
        limit (int, опционально): Ограничение количества результатов.

    Возвращает:
        List[Dict]: Список документов, отсортированных по расстоянию (ближайшие сначала).
                   Каждый документ содержит поле `distance` (расстояние в метрах).
    """

    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [user_lng, user_lat]  # Порядок: [longitude, latitude]
                },
                "distanceField": "distance_m",  # Добавляет поле с расстоянием
                "spherical": True,  # Учитывает сферичность Земли
                "key": "location"   # Поле с GeoJSON-точками
            }
        },
        {
            "$addFields": {
                "distance_km_rounded": {
                    "$round": [  # Округление до 1 десятичного знака
                        {"$divide": ["$distance_m", 1000]},  # Метры → километры
                        1
                    ]
                }
            }
        },
        {
            "$sort": {"distance_m": 1}  # Сортировка по возрастанию расстояния
        }
    ]

    # Опциональные параметры
    if max_distance is not None:
        pipeline[0]["$geoNear"]["maxDistance"] = max_distance

    if limit is not None:
        pipeline.append({"$limit": limit})

    results = list(collect.aggregate(pipeline))
    return results


def give_like(place_id, chat_id):
    place = collect.find_one({"_id": ObjectId(place_id)})
    if chat_id in place["likes_users_id"]:
        collect.update_one(
            {"_id": ObjectId(place_id)},
            {
                "$inc": {"likes": -1},
                "$pull": {"likes_users_id": chat_id},
            },
            upsert=True)
    else:
        if chat_id in place["dislikes_users_id"]:
            collect.update_one(
                {"_id": ObjectId(place_id)},
                {
                    "$inc": {"dislikes": -1},
                    "$pull": {"dislikes_users_id": chat_id},
                },
                upsert=True)
        collect.update_one(
            {"_id": ObjectId(place_id)},
            {
                "$addToSet": {"likes_users_id": chat_id},
                "$inc": {"likes": 1},
            },
            upsert=True)


def give_dislike(place_id, chat_id):
    place = collect.find_one({"_id": ObjectId(place_id)})
    if chat_id in place["dislikes_users_id"]:
        collect.update_one(
            {"_id": ObjectId(place_id)},
            {
                "$inc": {"dislikes": -1},
                "$pull": {"dislikes_users_id": chat_id},
            },
            upsert=True)
    else:
        if chat_id in place["likes_users_id"]:
            collect.update_one(
                {"_id": ObjectId(place_id)},
                {
                    "$inc": {"likes": -1},
                    "$pull": {"likes_users_id": chat_id},
                },
                upsert=True)
        collect.update_one(
            {"_id": ObjectId(place_id)},
            {
                "$addToSet": {"dislikes_users_id": chat_id},
                "$inc": {"dislikes": 1},
            },
            upsert=True)


def get_by_id(id: str):
    return collect.find_one({"_id": ObjectId(id)})


def find_by_name(name: str):
    return collect.find_one({"name": name})


def delete_by_name(name: str):
    collect.delete_one({"name": name})


def get_all(projection=None, args=None):
    if args is None:
        args = {}
    return collect.find(args, projection)


def delete_by_id(id: str):
    collect.delete_one({"_id": ObjectId(id)})


def get_with_photos_id(place_id):
    return collect.aggregate([
        {"$match": {
            "_id": place_id
        }},
        {"$lookup": {
            "from": "fs.files",
            "localField": "photos_id",
            "foreignField": "_id",
            "as": "photos",
        }},
    ])


def get_with_photos(stage):
    if stage:
        return collect.aggregate([
            stage,
            {"$lookup": {
                "from": "fs.files",
                "localField": "photos_id",
                "foreignField": "_id",
                "as": "photos",
            }},
        ])
    return collect.aggregate([
        {"$lookup": {
            "from": "fs.files",
            "localField": "photos_id",
            "foreignField": "_id",
            "as": "photos",
        }},
    ])
