import requests
import os
from dotenv import load_dotenv
import random


def download_random_comics():
    response = requests.get("https://xkcd.com/info.0.json")
    response.raise_for_status()
    total_comics_num = response.json()["num"]
    comics_num = random.randrange(total_comics_num)
    response = requests.get("https://xkcd.com/{}/info.0.json".format(comics_num))
    response.raise_for_status()
    reply = response.json()
    image_url = reply["img"]
    topic = reply["safe_title"]
    image_path = "{}.png".format(topic)
    comics_comment = reply["alt"]
    image = requests.get(image_url)
    response.raise_for_status()
    with open(image_path, "wb") as file:
        file.write(image.content)
    return image_path, comics_comment


def get_url_for_upload(access_token, group_id):
    payload = {"group_id": group_id, "v": 5.154}
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(
        "https://api.vk.com/method/photos.getWallUploadServer",
        params=payload,
        headers=headers
    )
    response.raise_for_status()
    reply = response.json()
    check_vk_api_errors(reply)
    upload_url = reply["response"]["upload_url"]
    return upload_url


def check_vk_api_errors(response):
    if "error" in response:
        print("Ошибка API VK")
        exit()


def upload_image_to_server(image_path, upload_url):
    with open(image_path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        reply = response.json()
        check_vk_api_errors(reply)
        comics_server = reply["server"]
        comics_hash = reply["hash"]
        comics_photo = reply["photo"]
    return comics_server, comics_hash, comics_photo


def save_image_to_album(comics_server, comics_hash, comics_photo, access_token, group_id):
    headers = {"Authorization": "Bearer {}".format(access_token)}
    payload = {
        "group_id": group_id,
        "v": 5.154,
        "server": comics_server,
        "hash": comics_hash,
        "photo": comics_photo
    }
    response = requests.get(
        "https://api.vk.com/method/photos.saveWallPhoto",
        params=payload,
        headers=headers
    )
    response.raise_for_status()
    reply = response.json()
    check_vk_api_errors(reply)
    owner_id = reply["response"][0]["owner_id"]
    media_id = reply["response"][0]["id"]
    return owner_id, media_id


def publish(owner_id, media_id, comics_comment, access_token, group_id):
    headers = {"Authorization": "Bearer {}".format(access_token)}
    payload = {
        "owner_id": -group_id,
        "v": 5.154,
        "attachments": "photo{}_{}".format(owner_id, media_id),
        "message": comics_comment
    }

    response = requests.post(
        "https://api.vk.com/method/wall.post",
        params=payload,
        headers=headers
    )
    response.raise_for_status()
    check_vk_api_errors(response.json())


if __name__ == "__main__":
    load_dotenv()
    image_path, comics_comment = download_random_comics()
    group_id = int(os.environ['GROUP_ID'])
    access_token = os.environ['ACCESS_TOKEN']
    upload_url = get_url_for_upload(access_token, group_id)
    comics_server, comics_hash, comics_photo = upload_image_to_server(image_path, upload_url)
    owner_id, media_id = save_image_to_album(
        comics_server,
        comics_hash,
        comics_photo,
        access_token,
        group_id
    )
    publish(owner_id, media_id, comics_comment, access_token, group_id)
    os.remove(image_path)