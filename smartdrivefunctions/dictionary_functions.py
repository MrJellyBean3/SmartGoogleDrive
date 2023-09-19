# Drive Imports
dictionaries_folder_path=""
structure_dictionary_path=""
information_dictionary_path=""
folder_dictionary_path=""

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import google_drive_functions as agf
import json
import aiohttp
import asyncio
import time
import yaml

BASE_URL = 'https://www.googleapis.com/drive/v3/files'

#Structure Dictionary
async def structure_dictionary_iterable(token, file_list=None, path=""):
    if file_list is None and path == "":
        file_list = await list_files(token, 'root')

    tasks = []

    for item in file_list:
        if "folder" in item['mimeType']:
            tasks.append(process_folder(token, item, path))
        else:
            tasks.append(process_file(token, item, path))

    results = await asyncio.gather(*tasks)
    
    # Collate results into a single dictionary
    contents_dict = {}
    for result in results:
        contents_dict.update(result)

    return contents_dict
async def process_folder(token, item, path):
    print(item['name'], item['mimeType'], item['id'])
    new_files_list = await list_files(token, item['id'])
    contents = await structure_dictionary_iterable(token, new_files_list, path + "/" + item['name'])
    
    return {
        item['name']: {
            "id": item['id'],
            "mimeType": item['mimeType'],
            "modifiedTime": format_date(item['modifiedTime']),
            "path": path,
            "contents": contents
        }
    }
async def process_file(token, item, path):
    print(item['name'], item['mimeType'], item['id'])
    if "shortcut" in item['mimeType']:
        file_metadata = await get_file_metadata(token, item["id"])
        actual_file_id = file_metadata['shortcutDetails']['targetId']
        actual_file = await fetch_metadata(token, actual_file_id)
        last_modified = format_date(actual_file['modifiedTime'])
        
        return {
            item['name']: {
                "id": actual_file['id'],
                "mimeType": actual_file['mimeType'],
                "modifiedTime": last_modified,
                "path": path
            }
        }
    else:
        last_modified = format_date(item['modifiedTime'])
        
        return {
            item['name']: {
                "id": item['id'],
                "mimeType": item['mimeType'],
                "modifiedTime": last_modified,
                "path": path
            }
        }
def format_date(date_str):
    return date_str.split("T")[0] + " " + date_str.split("T")[-1].split("Z")[0]

async def list_files(token, parent_id):
    params = {
        'q': f"'{parent_id}' in parents and trashed=false",
        'fields': 'files(id, mimeType, name, modifiedTime)'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, headers={"Authorization": f"Bearer {token}"}, params=params) as resp:
            data = await resp.json()
            if 'files' in data:
                return data['files']
            else:
                print(f"Error response from API: {data}")
                return []
async def get_file_metadata(token, file_id):
    params = {
        'fields': 'mimeType,shortcutDetails'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/{file_id}", headers={"Authorization": f"Bearer {token}"}, params=params) as resp:
            return await resp.json()
async def fetch_metadata(token, file_id):
    params = {
        'fields': 'id, mimeType, modifiedTime'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/{file_id}", headers={"Authorization": f"Bearer {token}"}, params=params) as resp:
            return await resp.json()






async def information_dictionary_iterable(creds, input_dict, information_dict=None):
    if information_dict is None:
        information_dict = {}

    tasks = []  # List to keep track of tasks

    for key, value in input_dict.items():
        if "contents" in value:  # Check for sub-folders
            tasks.append(information_dictionary_iterable(creds, value["contents"], information_dict))
        else:
            tasks.append(information_process_file(creds, key, value, information_dict))

    await asyncio.gather(*tasks)

    return information_dict


async def information_process_file(creds, key, value, information_dict):
    file_id = value["id"]
    if file_id not in information_dict:
        information_dict[file_id] = {
            "title": key,
            "id": file_id,
            "mimeType": value["mimeType"],
            "modifiedDate": value["modifiedTime"],
            "path": value["path"],
            "content": await get_content_based_on_type(creds, value),
            "mapped": False,
            "mapping": "",
            "mappedDate": ""
        }
    else:
        # Update existing entry
        information_dict[file_id].update({
            "title": key,
            "id": file_id,
            "mimeType": value["mimeType"],
            "modifiedDate": value["modifiedTime"],
            "path": value["path"],
            "content": await get_content_based_on_type(creds, value),
        })


async def get_content_based_on_type(creds,file_meta):
    if "document" in file_meta["mimeType"]:
        print("Document ", file_meta["id"])
        return await agf.get_from_docs(creds,file_meta["id"])  # Assuming this is now async
    elif "spreadsheet" in file_meta["mimeType"]:
        print("Sheet ", file_meta["id"])
        return await agf.get_from_sheets(creds,file_meta["id"])  # Assuming this is now async
    else:
        return None
    

def generate_folder_dictionary(structure_dict, information_dict,folder_dict=None):
    if folder_dict is None:
        folder_dict = {}

    def recursive_folder_processing(current_dict,key=""):
        base_key=key
        contained_folder_ids=[]
        contained_file_ids = []

        if "contents" in current_dict:
            for key, value in current_dict["contents"].items():
                # If the value contains a content key, it's a sub-folder
                if "contents" in value:
                    recursive_folder_processing(value,key)
                    contained_folder_ids.append(value["id"])
                else:
                    contained_file_ids.append(value["id"])

        # If this dictionary has an ID (it's a folder), update the folder_dict
        folder_id = current_dict.get("id")
        if folder_id:
            if folder_id not in folder_dict:
                folder_dict[folder_id]={}
            folder_dict[folder_id]["title"]=base_key
            folder_dict[folder_id]["id"]=folder_id
            folder_dict[folder_id]["mimeType"]=current_dict["mimeType"]
            folder_dict[folder_id]["modifiedDate"]=current_dict["modifiedTime"]
            folder_dict[folder_id]["contained_file_ids"]=contained_file_ids
            folder_dict[folder_id]["contained_folder_ids"]=contained_folder_ids
            folder_dict[folder_id]["path"]=current_dict["path"]
            if "mapping" not in folder_dict[folder_id]:
                folder_dict[folder_id]["mapping"]=""
            if "mappedDate" not in folder_dict[folder_id]:
                folder_dict[folder_id]["mappedDate"]=""
            if "mapped" not in folder_dict[folder_id]:
                folder_dict[folder_id]["mapped"]=False

    # Start the recursive process from the root of structure_dict
    for key, value in structure_dict.items():
        recursive_folder_processing(value,key)

    return folder_dict








# Use this function to initiate the process
def check_for_coroutines(obj, path=""):
    if asyncio.iscoroutinefunction(obj) or asyncio.iscoroutine(obj):
        print(f"Found coroutine at path: {path}")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            new_path = path + f"[{repr(key)}]"
            check_for_coroutines(key, new_path + " (key)")
            check_for_coroutines(value, new_path)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            check_for_coroutines(item, path + f"[{idx}]")


async def main(creds, processes_to_run):
    global dictionaries_folder_path, structure_dictionary_path, information_dictionary_path, folder_dictionary_path
    if not os.path.isdir(dictionaries_folder_path):
        os.mkdir(dictionaries_folder_path)
    YOUR_TOKEN = creds.token
    if "structure" in processes_to_run:
        #Run structure dictionary creation
        file_structure = await structure_dictionary_iterable(YOUR_TOKEN)
        with open(structure_dictionary_path, 'w') as outfile:
            yaml.dump(file_structure, outfile, default_flow_style=False)
        print("Finished Structure Dictionary Creation")
    if "information" in processes_to_run:
        #Run information dictionary creation
        with open(structure_dictionary_path, 'r') as file:
            structure_dictionary = yaml.load(file, Loader=yaml.FullLoader)
        if os.path.exists(information_dictionary_path):
            with open(information_dictionary_path, 'r') as file:
                information_dict = yaml.load(file, Loader=yaml.FullLoader)
        else:
            information_dict = None
        information_dict = await information_dictionary_iterable(creds,structure_dictionary,information_dict)
        check_for_coroutines(information_dict)
        with open(information_dictionary_path, 'w') as outfile:
            yaml.dump(information_dict, outfile, default_flow_style=False)
        print("Finished Information Dictionary Creation")

        #Run folder creation
        with open(structure_dictionary_path, "r") as file:
            structure_dictionary = yaml.load(file, Loader=yaml.FullLoader)
        with open(information_dictionary_path, "r") as file:
            information_dict = yaml.load(file, Loader=yaml.FullLoader)
        if os.path.exists(folder_dictionary_path):
            with open(folder_dictionary_path, "r") as file:
                folder_dictionary = yaml.load(file, Loader=yaml.FullLoader)
        else:
            folder_dictionary = None
        folder_dictionary = generate_folder_dictionary(structure_dictionary, information_dict,folder_dictionary)
        with open(folder_dictionary_path, "w") as file:
            yaml.dump(folder_dictionary, file, default_flow_style=False)
        print("Finished Folder Dictionary Creation")



