from bson.objectid import ObjectId
import env_variables
from database import db_client
from pymongo import collection
from database import categories

collect: collection = db_client[env_variables.db_name]["places"]


def add(name, photos_id, description, category_name, reviews=None):
    collect.insert_one({"name": name,
                        "photos_id": photos_id,
                        "description": description,
                        "category_id": categories.find_by_name(category_name)["_id"],
                        "likes_users_id": [],
                        "dislikes_users_id": [],
                        "reviews": reviews,
                        "likes": 0,
                        "dislikes": 0})


def update(place_id, name, photos_id, description, category_name, reviews=None):
    collect.update_one({"_id": ObjectId(place_id)},
                       {"$set": {"reviews": reviews,
                                 "name": name,
                                 "photos_id": photos_id,
                                 "description": description,
                                 "category_id": categories.find_by_name(category_name)["_id"]
                                 }})


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
