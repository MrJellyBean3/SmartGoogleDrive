# Drive Imports
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import gdrive_functions as gf
import json



# Create structure dictionary
def structure_dictionary_iterable(drive,drive_service,file_list=[],path=""):
    #create dictionary
    if file_list==[] and path=="":
        file_list=drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    file_structure_dict={}

    #loop through file list
    for item in file_list:
        #If a folder is found make a new dictionary
        if "folder" in item['mimeType']:
            print(item['title'],item['mimeType'],item['id'])
            new_files_list=drive.ListFile({'q': "'{}' in parents and trashed=false".format(item['id'])}).GetList()
            file_structure_dict[item['title']]=structure_dictionary_iterable(drive,drive_service,new_files_list,path+"/"+item['title'])
        #Otherwise add the file to the dictionary
        else:
            print(item['title'],item['mimeType'],item['id'])
            if "shortcut" in item['mimeType']:
                file_metadata = drive_service.files().get(fileId=item["id"], fields='mimeType,shortcutDetails').execute()
                actual_file_id = file_metadata['shortcutDetails']['targetId']

                actual_file = drive.CreateFile({'id': actual_file_id})
                actual_file.FetchMetadata()

                #format last modified
                last_modified_not_formatted=actual_file['modifiedDate']
                last_modified=last_modified_not_formatted.split("T")[0]+" "+last_modified_not_formatted.split("T")[-1].split("Z")[0]

                #add to dictionary
                file_structure_dict[item['title']]={"id":actual_file['id'],"mimeType":actual_file['mimeType'],"modifiedDate":last_modified,"path":path}

            else:
                #format last modified
                last_modified_not_formatted=item['modifiedDate']
                last_modified=last_modified_not_formatted.split("T")[0]+" "+last_modified_not_formatted.split("T")[-1].split("Z")[0]

                #add to dictionary
                file_structure_dict[item['title']]={"id":item['id'],"mimeType":item['mimeType'],"modifiedDate":last_modified,"path":path}
    return file_structure_dict



# Create information dictionary
def information_dictionary_iterable(input_dictionary,information_dict,docs_service,sheet_service):
    for key in list(input_dictionary.keys()):
        if (type(input_dictionary[key])==dict) and not ("mimeType" in list(input_dictionary[key].keys())):
            information_dict=information_dictionary_iterable(input_dictionary[key],information_dict,docs_service,sheet_service)
        else:
            #check if the key id is already in the dictionary
            if str(input_dictionary[key]["id"]) in list(information_dict.keys()):
                information_dict[str(input_dictionary[key]["id"])]["title"]=key
                information_dict[str(input_dictionary[key]["id"])]["id"]=input_dictionary[key]["id"]
                information_dict[str(input_dictionary[key]["id"])]["mimeType"]=input_dictionary[key]["mimeType"]
                information_dict[str(input_dictionary[key]["id"])]["modifiedDate"]=input_dictionary[key]["modifiedDate"]
                information_dict[str(input_dictionary[key]["id"])]["path"]=input_dictionary[key]["path"]
                if "document" in input_dictionary[key]["mimeType"]:
                    information_dict[str(input_dictionary[key]["id"])]["content"]=gf.get_from_docs(docs_service,input_dictionary[key]["id"])
                elif "spreadsheet" in input_dictionary[key]["mimeType"]:
                    information_dict[str(input_dictionary[key]["id"])]["content"]=gf.get_from_sheets(sheet_service,input_dictionary[key]["id"])
            else:
                information_dict[str(input_dictionary[key]["id"])]={}
                information_dict[str(input_dictionary[key]["id"])]["title"]=key
                information_dict[str(input_dictionary[key]["id"])]["id"]=input_dictionary[key]["id"]
                information_dict[str(input_dictionary[key]["id"])]["mimeType"]=input_dictionary[key]["mimeType"]
                information_dict[str(input_dictionary[key]["id"])]["modifiedDate"]=input_dictionary[key]["modifiedDate"]
                information_dict[str(input_dictionary[key]["id"])]["path"]=input_dictionary[key]["path"]
                if "document" in input_dictionary[key]["mimeType"]:
                    information_dict[str(input_dictionary[key]["id"])]["content"]=gf.get_from_docs(docs_service,input_dictionary[key]["id"])
                elif "spreadsheet" in input_dictionary[key]["mimeType"]:
                    information_dict[str(input_dictionary[key]["id"])]["content"]=gf.get_from_sheets(sheet_service,input_dictionary[key]["id"])
                else:
                    information_dict[str(input_dictionary[key]["id"])]["content"]=None
                information_dict[str(input_dictionary[key]["id"])]["mapped"]=False
                information_dict[str(input_dictionary[key]["id"])]["mapping"]=""
                information_dict[str(input_dictionary[key]["id"])]["mappedDate"]=""
    return information_dict



# # Update the mapping
# def update_mapping(your_dictionary,override=False):
#     data_text=""
#     # Check if 'mappedDate' key exists and if it's out of date or empty
#     for key in list(your_dictionary.keys()):
#         data_text+="This is document "+your_dictionary[key]["id"]+"with title-"+your_dictionary[key]["title"]+":\n{'"
#         data_text+=your_dictionary[key]["content"]+"'}\nEnd of document with title-"+your_dictionary[key]["title"]+"\n\n"

#         if override or 'mappedDate' not in your_dictionary[key] or not your_dictionary[key]['mappedDate'] or your_dictionary[key]['modifiedDate'] > your_dictionary[key]['mappedDate']:
#             # Call the generate_mapping function to generate mapping based on content
#             mapping = generate_mapping(your_dictionary[key]['content'],your_dictionary[key]['title'],your_dictionary[key]['path'])
#             print("MAPP: ",mapping)
#             # Update the dictionary with the new mapping and set the mappedDate to the current modifiedDate
#             your_dictionary[key]['mapping'] = mapping
#             your_dictionary[key]['mapped']=True
#             your_dictionary[key]['mappedDate'] = your_dictionary[key]['modifiedDate']
    
#     with open("database_text.txt",'w', encoding='utf-8') as f:
#         f.write(data_text)

#     return your_dictionary


