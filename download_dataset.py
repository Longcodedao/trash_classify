import requests
import zipfile

import os 

def download_file(url, dest_folder):
    try:
        print('Attempting download from:', url)
        response = requests.get(url, stream = True)
        response.raise_for_status()  # Check for HTTP errors

        os.makedirs(dest_folder, exist_ok = True)

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        destination = os.path.join(dest_folder, url.split('/')[-1])
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size = 8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    if total_size > 0:
                        done = int(50 * downloaded_size / total_size)
                        print(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded_size}/{total_size} bytes", end='')
        print('\nDownload completed:', destination)
    except requests.exceptions.RequestException as e:
        print('Download failed:', e)


def unzip_file(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print('Extraction completed:', extract_to)
    except zipfile.BadZipFile as e:
        print('Extraction failed:', e)


if __name__ == "__main__":
    url = "https://github.com/garythung/trashnet/raw/refs/heads/master/data/dataset-resized.zip"
    dest_folder = "./data"

    download_path = os.path.join(dest_folder, url.split('/')[-1])
    if os.path.exists(download_path):
        print('File already exists. Skipping download.')
    else:
        download_file(url, dest_folder)

    unzip_file(download_path, dest_folder)
    remove_zip = input('Do you want to delete the zip file? (y/n): ')
    if remove_zip.lower() == 'y':
        os.remove(download_path)
        print('Zip file deleted.')


    