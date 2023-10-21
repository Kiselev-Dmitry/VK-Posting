import os


def save_file(image, image_path):
    with open(image_path, "wb") as file:
        file.write(image.content)


def delete_file(image_path):
    os.remove(image_path)
