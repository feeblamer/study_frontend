import argparse
import os
import re
import sys
import zipfile
from mimetypes import guess_extension
from urllib.parse import unquote

import requests


def create_session(token):
    s = requests.Session()
    s.headers.update({'Accept': 'application/json', 'Authorization': 'OAuth {}'.format(token)})
    return s

def get_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', required=True, help='Путь до файла на яндекс диске')
    parser.add_argument('-t', '--token', required=True, help='Токен API')
    return parser.parse_args(args)


def get_disk_info(s):
    url = 'https://cloud-api.yandex.net/v1/disk'
    r = s.get(url)
    return r

def get_direct_link_to_file(s, path):
    base_url = 'https://cloud-api.yandex.net/v1/disk/resources/download?path={}'
    url = base_url.format(path)
    r = s.get(url)
    if r.ok:
        return r.json()['href']

def get_filename(r):
    print('ЗАГОЛОВКИ: {}'.format(r.headers['Content-Disposition']))
    filename_pattern = re.compile(r"(?<=filename\*=UTF-8'').*$")
    print(r.headers['Content-Disposition'])
    if "Content-Disposition" in r.headers and "filename" in r.headers["Content-Disposition"]:
        filename = filename_pattern.search(r.headers['Content-Disposition'])[0]
        return unquote(filename)
    else:
        url = r.url.split("?")[0]
        filename = url.rstrip("/").split("/")[-1]
        if re.findall(r'\.[a-zA-Z]{2}[\w]{0,2}$', filename):
            return unquote(filename)
        else:
            content_type =r.headers["Content-Type"]
            content_type = re.findall(r'([a-z]{4,11}/[\w\+\-\.]+)', content_type)[0]
            if "Content-Type" in r.headers and guess_extension(content_type):
                filename = filename + guess_extension(content_type)
                return unquote(filename)
            else: 
                return unquote(filename)


def download_file(direct_link):
    r = requests.get(direct_link)
    if r.ok:
        filename = get_filename(r)
        print('Будет записан фалй {}'.format(filename))
        with open(filename, 'wb') as f:
            f.write(r.content)
        return filename


def main(session, args):
    link = get_direct_link_to_file(session, args.path)
    print(link)
    filename = download_file(link)
    with zipfile.ZipFile(filename, 'r') as zf:
        zf.extractall()
    os.remove(filename)

if __name__ == '__main__':
    args = get_args(sys.argv[1:])
    print(args.token)
    s = create_session(args.token)
    main(s, args)
