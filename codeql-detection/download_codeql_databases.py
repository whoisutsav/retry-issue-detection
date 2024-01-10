#!/usr/bin/python3

import requests
import os
import tempfile
from zipfile import ZipFile
from tqdm import tqdm

## Script created with GPT ##

CHUNK_SIZE = 8192 

def download_file(url, destination):
    with requests.get(url, stream=True) as response:
        total_size = int(response.headers.get('content-length', 0))
        progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)

        with open(destination, 'wb') as file:
            for chunk in response.iter_content(CHUNK_SIZE):
                progress_bar.update(len(chunk))
                file.write(chunk)

        progress_bar.close()
        print(f"\nDownloaded {url} as {destination}")

def unzip_file(zip_path, extract_path):
    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        print(f"Unzipped {zip_path} to {extract_path}")

def delete_file(file_path):
    os.remove(file_path)
    print(f"Deleted {file_path}")

def download_and_unzip(files_to_download, extract_dir):
    os.makedirs(extract_dir, exist_ok=True)

    for file_info in files_to_download:
        file_name = file_info.get("file_name")
        link = file_info.get("link")

        if file_name and link:
            temp_dir = tempfile.gettempdir()
            download_path = os.path.join(temp_dir, file_name)
            unzip_path = extract_dir 

            print(f"\nDownloading {file_name}...")
            download_file(link, download_path)

            print(f"\nUnzipping {file_name}...")
            unzip_file(download_path, unzip_path)

            print(f"\nDeleting {file_name}...")
            delete_file(download_path)
        else:
            print("Invalid dictionary format. Skipping.")

if __name__ == "__main__":
    files_to_download = [
        {"file_name": "apache_cassandra_f0ad7ea.zip", "link": "https://uchicago.box.com/shared/static/skmk1pfqgdq1ufeu4qwxatj0tolnhvqg"},
        {"file_name": "apache_hadoop_ee7d178.zip", "link": "https://uchicago.box.com/shared/static/rmpajmi1jrkwr8he342cylwt1x6rlehn"},
        {"file_name": "apache_hbase_e1ad781.zip", "link": "https://uchicago.box.com/shared/static/2moclv0kvfim6hezaqft0x5im3zlz82g"},
        {"file_name": "apache_hive_e427ce0.zip", "link": "https://uchicago.box.com/shared/static/ca10vugmln74rtotsr916kudiqji5nqe"},
        {"file_name": "elastic_elasticsearch_7556157.zip", "link": "https://uchicago.box.com/shared/static/c07ttbpn8j58cv4ob02a2sthimkd27ez"},
    ]

    # Directory for extracted files
    extract_dir = "databases"

    # Download, unzip, and delete files with progress meter and status updates
    download_and_unzip(files_to_download, extract_dir)

