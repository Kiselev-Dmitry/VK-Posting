import requests
import os
from dotenv import load_dotenv
import random


def download_random_comic():
    response = requests.get("https://xkcd.com/info.0.json")
    response.raise_for_status()
    total_comics_num = response.json()["num"]
    comic_num = random.randrange(total_comics_num)
    response = requests.get("https://xkcd.com/{}/info.0.json".format(comic_num))
    response.raise_for_status()
    json_content = response.json()
    image_url = json_content["img"]
    topic = json_content["safe_title"]
    image_path = "{}.png".format(topic)
    comic_comment = json_content["alt"]
    image = requests.get(image_url)
    response.raise_for_status()
    with open(image_path, "wb") as file:
        file.write(image.content)
    return image_path, comic_comment


def get_url_for_upload(tg_token, tg_group_id):
    payload = {"access_token": tg_token, "group_id": tg_group_id, "v": 5.154}
    response = requests.get(
        "https://api.vk.com/method/photos.getWallUploadServer",
        params=payload,
    )
    response.raise_for_status()
    json_content = response.json()
    check_vk_api_errors(json_content)
    upload_url = json_content["response"]["upload_url"]
    return upload_url


def check_vk_api_errors(json_content):
    if "error" in json_content:
        raise requests.exceptions.HTTPError


def upload_image_to_server(image_path, upload_url):
    with open(image_path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    json_content = response.json()
    check_vk_api_errors(json_content)
    comic_server = json_content["server"]
    comic_hash = json_content["hash"]
    comic_photo = json_content["photo"]
    return comic_server, comic_hash, comic_photo


def save_image_to_album(comic_server, comic_hash, comic_photo, tg_token, tg_group_id):
    payload = {
        "access_token": tg_token,
        "group_id": tg_group_id,
        "v": 5.154,
        "server": comic_server,
        "hash": comic_hash,
        "photo": comic_photo
    }
    response = requests.get(
        "https://api.vk.com/method/photos.saveWallPhoto",
        params=payload,
    )
    response.raise_for_status()
    json_content = response.json()
    check_vk_api_errors(json_content)
    owner_id = json_content["response"][0]["owner_id"]
    media_id = json_content["response"][0]["id"]
    return owner_id, media_id


def publish(owner_id, media_id, comic_comment, tg_token, tg_group_id):
    payload = {
        "access_token": tg_token,
        "owner_id": -tg_group_id,
        "v": 5.154,
        "attachments": "photo{}_{}".format(owner_id, media_id),
        "message": comic_comment
    }

    response = requests.post(
        "https://api.vk.com/method/wall.post",
        params=payload,
    )
    response.raise_for_status()
    check_vk_api_errors(response.json())


if __name__ == "__main__":
    load_dotenv()
    try:
        image_path, comic_comment = download_random_comic()
        tg_group_id = int(os.environ['TG_GROUP_ID'])
        tg_token = os.environ['TG_TOKEN']
        upload_url = get_url_for_upload(tg_token, tg_group_id)
        comic_server, comic_hash, comic_photo = upload_image_to_server(image_path, upload_url)
        owner_id, media_id = save_image_to_album(
            comic_server,
            comic_hash,
            comic_photo,
            tg_token,
            tg_group_id
        )
        publish(owner_id, media_id, comic_comment, tg_token, tg_group_id)
    except:
        print("Возникла ошибка. Повторите еще раз.")
    finally:
        os.remove(image_path)
