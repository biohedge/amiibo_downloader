# Amiibo API crawler
import requests
import os
import binascii
import json
from datetime import datetime

OUTPUT_DIR = './amiibo'

API_URL = 'https://www.amiiboapi.com/api/amiibo/'

AMIIBO_FILE = 'amiibo.json'
AMIIBO_IMAGE = 'amiibo.png'
AMIIBO_FLAG = 'amiibo.flag'


def convert_api_item(item):
    return {
        "name": item.get("name"),
        "series": item.get("amiiboSeries"),
        "character": item.get("character"),
        "image_url": item.get("image"),
        "id": item.get("head") + item.get("tail"),
    }


def fetch_data_from_api():
    response = requests.get(API_URL).json()
    data = response.get('amiibo')
    if data is None:
        raise('Empty response from server')

    data.sort(key=lambda x: x.get('name'))
    return [convert_api_item(item) for item in data]


def process_data(amibo_data):
    for amiibo in amibo_data:
        try:
            save_amiibo(amiibo)
        except Exception as e:
            print(f'Failed to save amiibo {amiibo}: {e}')


def save_amiibo(amiibo):
    res_obj = get_amiibo_obj(amiibo)

    series = amiibo.get('series')
    if series is None:
        raise(f'Empty series for {amiibo}')
    name = amiibo.get('name')
    if series is None:
        raise(f'Empty name for {amiibo}')

    id_str = amiibo.get('id')
    if id_str is None:
        raise(f'Empty id for {amiibo}')

    output_dir = f'{OUTPUT_DIR}/{series}/{name} ({id_str})'

    if os.path.exists(output_dir):
        print(f'Already exist: {output_dir}')
        return

    print(f'Creating: {output_dir}')
    os.makedirs(output_dir, exist_ok=True)

    image_url = amiibo.get('image_url')
    if image_url is not None:
        image = get_image(image_url)

    save_files(res_obj, image, output_dir)


def get_id(amiibo):
    id_string = amiibo.get('id')
    char_id_str = id_string[:4]
    char_var_str = id_string[4:6]
    fig_type_str = id_string[6:8]
    model_no_str = id_string[8:12]
    series_str = id_string[12:14]

    char_id_int = int(char_id_str, 16)
    char_id_bytes = char_id_int.to_bytes(2, 'big')

    return {
        'game_character_id': int.from_bytes(char_id_bytes, byteorder='little'),
        'character_variant': int(char_var_str, 16),
        'figure_type': int(fig_type_str, 16),
        'series': int(series_str, 16),
        'model_number': int(model_no_str, 16)
    }


def get_date():
    now_date = datetime.now().date()

    return {
        'y': now_date.year,
        'm': now_date.month,
        'd': now_date.day
    }


def get_uuid():
    rnd_bytes = bytearray(os.urandom(6))
    rnd_bytes.extend([0, 0, 0])

    return list(rnd_bytes)


def get_amiibo_obj(amiibo):
    curr_date = get_date()
    return {
        'name': amiibo.get('name'),
        'write_counter': 0,
        'version': 0,
        'mii_charinfo_file': 'mii-charinfo.bin',
        'first_write_date': curr_date,
        'last_write_date': curr_date,
        'id': get_id(amiibo),
        'uuid': get_uuid()
    }


def get_image(image_url):
    image = requests.get(image_url)
    return image.content


def save_files(amiibo, image, output_dir):
    amiibo_file = f'{output_dir}/{AMIIBO_FILE}'
    with open(amiibo_file, 'w') as f:
        f.write(json.dumps(amiibo))

    flag_file = f'{output_dir}/{AMIIBO_FLAG}'
    with open(flag_file, 'w') as f:
        pass

    image_file = f'{output_dir}/{AMIIBO_IMAGE}'
    if image is not None:
        with open(image_file, 'wb') as f:
            f.write(image)


def download_amiibos():
    try:
        amibo_data = fetch_data_from_api()
        process_data(amibo_data)
    except Exception as e:
        print(f'Failed to get data {e}')


if __name__ == "__main__":
    download_amiibos()
