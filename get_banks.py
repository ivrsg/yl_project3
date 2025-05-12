import json
from io import BytesIO
import requests
from PIL import Image
from geopy.distance import great_circle
import os


def find_bank(toponym_to_find):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
        "geocode": toponym_to_find,
        "format": "json"}
    response = requests.get(geocoder_api_server, params=geocoder_params)
    if not response:
        pass
    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    toponym_coodrinates = toponym["Point"]["pos"]
    point = ",".join(toponym_coodrinates.split())
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    apikey = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
    address_ll = point
    search_params = {
        "apikey": api_key,
        "text": "банкомат",
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz"
    }
    pharmacy_response = requests.get(search_api_server, params=search_params)
    json_pharmacy_response = pharmacy_response.json()
    if not response:
        print("Банкомат не найден")
    s = ''
    pointsx = []
    pointsy = []
    for t, i in enumerate(json_pharmacy_response["features"][:10]):
        organization = i
        org_name = organization["properties"]["CompanyMetaData"]["name"]
        org_address = organization["properties"]["CompanyMetaData"]["address"]
        org_hours = organization["properties"]["CompanyMetaData"]["Hours"]["text"]
        point_pharm = organization["geometry"]["coordinates"]
        distance = great_circle((float(point_pharm[0]), float(point_pharm[1])),
                                (float(point.split(',')[0]), float(point.split(',')[1]))).meters
        s += f',~{point_pharm[0]},{point_pharm[1]},pm2dgm{t + 1}'
        pointsx.append(point_pharm[0])
        pointsy.append(point_pharm[1])

    p1 = [min(pointsx), min(pointsy)]
    p2 = [max(pointsx), max(pointsy)]
    p3 = [str(p2[0] - p1[0]), str(p2[1] - p1[1])]
    map_params = {
        "apikey": apikey,
        "pt": f"{toponym_longitude},{toponym_lattitude},pm2rdl{s}",
        'll': f"{toponym_longitude},{toponym_lattitude}",
        'size': '650,450',
        'spn': f'{",".join(p3)}'
    }
    map_api_server = "https://static-maps.yandex.ru/v1"
    response = requests.get(map_api_server, params=map_params)
    im = BytesIO(response.content)
    opened_image = Image.open(im)
    try:
        opened_image.save('static/img/map.png')
    except FileNotFoundError:
        os.mkdir('static/img')
        opened_image.save('static/img/map.png')
