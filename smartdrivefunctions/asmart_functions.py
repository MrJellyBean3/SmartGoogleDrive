print("import begin")
import time
t_s_abs=time.time()
import yaml
import asyncio
from deferred_imports import langchain, imports_done
import webbrowser
print("import end: ",time.time()-t_s_abs)






# Information Mapping
async def a_update_mapping(your_dictionary,override=False):
    tasks=[]
    for key in list(your_dictionary.keys()):
        if override or 'mappedDate' not in your_dictionary[key] or not your_dictionary[key]['mappedDate'] or your_dictionary[key]['modifiedDate'] > your_dictionary[key]['mappedDate']:
            tasks.append(a_generate_mapping(your_dictionary[key]['content'],your_dictionary[key]['title'],your_dictionary[key]['path'],key))

    results=await asyncio.gather(*tasks)
    for item in results:
        id=list(item.keys())[0]
        your_dictionary[id]['mapping'] = item[id]
        your_dictionary[id]['mapped']=True
        your_dictionary[id]['mappedDate'] = your_dictionary[id]['modifiedDate']

    return your_dictionary
async def a_generate_mapping(content,title,parent,id):
    imports_done.wait()
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts.chat import (
        ChatPromptTemplate,
        SystemMessagePromptTemplate,
        HumanMessagePromptTemplate,
    )
    # Define the templates
    system_template="I want you to give a summary of the of the document the user gives you as if you were describing it and what it is for, the user will also tell you the path of the parent directory of the document and its title which you should use to understand what the summary should be, for example a 'book summaries' document's summary should include that it is a summary of books and not simply the contents of the books."
    human_template="Here is my document title-{title}, with parent directory-{parent}, and here is content of the document:\n{content}"
    system_template2="""You are to provide a useful summary and description so that someone reading your description would know what you are refering to. Use the context of the title and parent directory to understand what the description and summary should be. Think before begin to describe the document. Break down the path into sections splitting with each \\ and think about them out loud, tell me what the meaning of each directory is in your interpretation. After you are finished thinking give your description . Your response should follow this template:
    \"'Thoughts: 'what your thoughts are on the meaning of the document are and what it is for with relation to its title and parent directory'
    Description: 'your description and summary based on your thoughts so someone would know what this is for'\""""

    # Create the prompt
    system_message=SystemMessagePromptTemplate.from_template(system_template)
    human_message=HumanMessagePromptTemplate.from_template(human_template)
    system_message2=SystemMessagePromptTemplate.from_template(system_template2)
    message_list=[system_message,human_message,system_message2]
    chat_prompt=ChatPromptTemplate.from_messages(message_list)


    # Generate the mapping
    formated_prompt=chat_prompt.format_prompt(content=content, title=title, parent=parent).to_messages()
    raw_string_prompt=""
    for item in formated_prompt:
        raw_string_prompt+=item.type+": "+item.content+"\n\n"
    if len(raw_string_prompt)>9000:
        model_name="gpt-3.5-turbo-16k"
    else:
        model_name="gpt-3.5-turbo"
    chat=ChatOpenAI(model=model_name,temperature=0.3)
    chat_response=await chat.agenerate([formated_prompt])
    print(title+" "+parent+" "+chat_response.generations[0][0].text+"\n\n")
    output_string=chat_response.generations[0][0].text

    # Parse the mapping
    mapped_result=""
    mapped_result=(output_string).split("Description: ")[-1]
    if mapped_result=="":
        mapped_result=(output_string).split("Description:")[-1]
    return {id:mapped_result}





# Folder Mapping
async def a_update_folder_mapping(folder_dictionary,information_dictionary,override=False):
    finished_folders=[]
    length_folders=len(list(folder_dictionary.keys()))
    results=[]
    while(length_folders>len(finished_folders)):
        tasks=[]
        print("finished folders: "+str(len(finished_folders))+"/"+str(length_folders))
        for key in list(folder_dictionary.keys()):
            #check if the key is already mapped
            if not override and 'mappedDate' in folder_dictionary[key] and folder_dictionary[key]['mappedDate'] and folder_dictionary[key]['modifiedDate'] <= folder_dictionary[key]['mappedDate']:
                finished_folders.append(key)
                print("Already done: "+key)
            else:
                print("Not done: "+key, override, 'mappedDate' in folder_dictionary[key], folder_dictionary[key]['mappedDate'], folder_dictionary[key]['modifiedDate'] <= folder_dictionary[key]['mappedDate'])

            if key not in finished_folders:
                if folder_dictionary[key]["contained_folder_ids"]==[]:
                    #Create task
                    contents=""
                    for file_id in folder_dictionary[key]["contained_file_ids"]:
                        contents+=(information_dictionary[file_id]["mapping"])+"\n"
                    for folder_id in folder_dictionary[key]["contained_folder_ids"]:
                        contents+=(folder_dictionary[folder_id]["mapping"])+"\n"
                    tasks.append(a_generate_folder_mapping(contents,folder_dictionary[key]['title'],folder_dictionary[key]['path'],key))
                    finished_folders.append(key)
                else:
                    all_completed=True
                    for cf in folder_dictionary[key]["contained_folder_ids"]:
                        if cf not in finished_folders:
                            all_completed=False
                    if all_completed:
                        #Create task
                        contents=""
                        for file_id in folder_dictionary[key]["contained_file_ids"]:
                            contents+=(information_dictionary[file_id]["mapping"])+"\n"
                        for folder_id in folder_dictionary[key]["contained_folder_ids"]:
                            contents+=(folder_dictionary[folder_id]["mapping"])+"\n"
                        tasks.append(a_generate_folder_mapping(contents,folder_dictionary[key]['title'],folder_dictionary[key]['path'],key))
                        finished_folders.append(key)
        results.append(await asyncio.gather(*tasks))

    for result in results:
        for item in result:
            id=list(item.keys())[0]
            folder_dictionary[id]['mapping'] = item[id]
            folder_dictionary[id]['mapped']=True
            folder_dictionary[id]['mappedDate'] = folder_dictionary[id]['modifiedDate']
    return(folder_dictionary)
async def a_generate_folder_mapping(contents,title,parent,id):
    imports_done.wait()
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts.chat import (
        ChatPromptTemplate,
        SystemMessagePromptTemplate,
        HumanMessagePromptTemplate,
    )
    # Define the templates
    system_template="I want you to give a summary of the of the folder the user gives you as if you were describing it and what it is for, the user will also tell you the path of the parent directory of the folder, the folder title, and the descriptions of the contents of the files or folders the folder contains which you should use to understand what the description should be."
    human_template="Here is my folder title-{title}, with parent directory-{parent}, and here are the contents of the folder:\n{contents}"
    system_template2="""You are to provide a useful summary and description so that someone reading your description would know what you are refering to. Use the context of the title and parent directory to understand what the description and summary should be. Think before you begin to describe the document. Break down the path into sections splitting with each \\ and think about them out loud, tell me what the meaning of each directory is in your interpretation. After you are finished thinking give your description . Your response should follow this template:
    \"'Thoughts: 'what your thoughts are on the meaning of the folder are and what it is for with relation to its title and parent directory'
    Description: 'your description and summary based on your thoughts so someone would know what this is for'\""""

    # Create the prompt
    system_message=SystemMessagePromptTemplate.from_template(system_template)
    human_message=HumanMessagePromptTemplate.from_template(human_template)
    system_message2=SystemMessagePromptTemplate.from_template(system_template2)
    message_list=[system_message,human_message,system_message2]
    chat_prompt=ChatPromptTemplate.from_messages(message_list)


    # Generate the mapping
    formated_prompt=chat_prompt.format_prompt(contents=contents, title=title, parent=parent).to_messages()
    raw_string_prompt=""
    for item in formated_prompt:
        raw_string_prompt+=item.type+": "+item.content+"\n\n"
    if len(raw_string_prompt)>9000:
        model_name="gpt-3.5-turbo-16k"
    else:
        model_name="gpt-3.5-turbo"
    chat=ChatOpenAI(model=model_name,temperature=0.3)
    chat_response=await chat.agenerate([formated_prompt])
    print(title+" "+parent+" "+chat_response.generations[0][0].text+"\n\n")
    output_string=chat_response.generations[0][0].text

    # Parse the mapping
    mapped_result=(output_string).split("Description: ")[-1]
    if mapped_result=="":
        mapped_result=(output_string).split("Description:")[-1]
    return {id:mapped_result}






# Generate Mappings
def map(override=False):
    #map information
    information_dict_file_name="ainformation_dictionary.yaml"
    folder_dict_file_name="afolder_dictionary.yaml"
    with open(information_dict_file_name, "r") as file:
            information_dict = yaml.load(file, Loader=yaml.FullLoader)
    information_dict=asyncio.run(a_update_mapping(information_dict,override=override))
    with open(information_dict_file_name, 'w') as outfile:
        yaml.dump(information_dict, outfile)

    #map the folders
    with open(information_dict_file_name, "r") as file:
            information_dict = yaml.load(file, Loader=yaml.FullLoader)
    with open(folder_dict_file_name, "r") as file:
        folder_dictionary = yaml.load(file, Loader=yaml.FullLoader)
    folder_dictionary=asyncio.run(a_update_folder_mapping(folder_dictionary,information_dict,override=False))
    with open("afolder_dictionary.yaml", 'w') as outfile:
        yaml.dump(folder_dictionary, outfile)
    print("Done mapping")







# Update Database
def update_vectordb(persist_directory,finish_que):
    imports_done.wait()
    from langchain.vectorstores import Chroma
    from langchain.embeddings import OpenAIEmbeddings
    #read from information dictionary
    if "information" in persist_directory:
        base_dict_file_name="ainformation_dictionary.yaml"
    elif "folder" in persist_directory:
        base_dict_file_name="afolder_dictionary.yaml"
    with open(base_dict_file_name) as f:
        base_dict = yaml.load(f, Loader=yaml.FullLoader)
    #Create custom documents
    class Document:
        def __init__(self, page_content="",source="",dict_id="",mimeType="",title=""):
            self.page_content = page_content
            self.metadata={'source': source, 'id': dict_id, "mimeType":mimeType,"title":title}
        def __repr__(self):
            attributes = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
            return f"Document({attributes})"
    #Create list of documents
    my_documents = []
    for key in list(base_dict.keys()):
        if base_dict[key]["path"]=="":
            my_documents.append(Document(base_dict[key]["mapping"],source=base_dict[key]["path"]+"none id:"+base_dict[key]["id"]+":mimeType:"+base_dict[key]["mimeType"], dict_id=base_dict[key]["id"],mimeType=base_dict[key]["mimeType"],title=base_dict[key]["title"]))
        else:
            my_documents.append(Document(base_dict[key]["mapping"],source=base_dict[key]["path"]+" id:"+base_dict[key]["id"]+":mimeType:"+base_dict[key]["mimeType"], dict_id=base_dict[key]["id"],mimeType=base_dict[key]["mimeType"],title=base_dict[key]["title"]))
    #Delete and regenerate the database
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectordb = Chroma(persist_directory=persist_directory, 
                    embedding_function=embedding)
    try:
        vectordb.delete_collection()
        vectordb.persist()
    except Exception as e:
        print(e)
    vectordb = Chroma.from_documents(
        documents=my_documents, 
        embedding=embedding,
        persist_directory=persist_directory
    )
    vectordb.persist()
    vectordb = None
    finish_que.put(True)

def combine_vectordb(persist_directory):
    imports_done.wait()
    from langchain.vectorstores import Chroma
    from langchain.embeddings import OpenAIEmbeddings
    #read from information dictionary
    information_dict_file_name="ainformation_dictionary.yaml"
    folder_dict_file_name="afolder_dictionary.yaml"
    with open(information_dict_file_name) as f:
        information_dict = yaml.load(f, Loader=yaml.FullLoader)
    with open(folder_dict_file_name) as f:
        folder_dict = yaml.load(f, Loader=yaml.FullLoader)
    #Create custom documents
    class Document:
        def __init__(self, page_content="",source="",dict_id="",mimeType="",title=""):
            self.page_content = page_content
            self.metadata={'source': source, 'id': dict_id, "mimeType":mimeType,"title":title}
        def __repr__(self):
            attributes = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
            return f"Document({attributes})"
    #Create list of documents
    def add_documents(base_dict):
        my_documents = []
        for key in list(base_dict.keys()):
            if base_dict[key]["path"]=="":
                my_documents.append(Document(base_dict[key]["mapping"],source=base_dict[key]["path"]+"none id:"+base_dict[key]["id"]+":mimeType:"+base_dict[key]["mimeType"], dict_id=base_dict[key]["id"],mimeType=base_dict[key]["mimeType"],title=base_dict[key]["title"]))
            else:
                my_documents.append(Document(base_dict[key]["mapping"],source=base_dict[key]["path"]+" id:"+base_dict[key]["id"]+":mimeType:"+base_dict[key]["mimeType"], dict_id=base_dict[key]["id"],mimeType=base_dict[key]["mimeType"],title=base_dict[key]["title"]))
        return(my_documents)
    my_documents=add_documents(information_dict)+add_documents(folder_dict)
    #Delete and regenerate the database
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectordb = Chroma(persist_directory=persist_directory, 
                    embedding_function=embedding)
    try:
        vectordb.delete_collection()
        vectordb.persist()
    except Exception as e:
        print(e)
    vectordb = Chroma.from_documents(
        documents=my_documents, 
        embedding=embedding,
        persist_directory=persist_directory
    )
    vectordb.persist()
    vectordb = None
    print("Finished combining databases")

# Retrieve From Information
def retrieve_from_information(user_question,return_que):
    imports_done.wait()
    from langchain.vectorstores import Chroma
    from langchain.embeddings import OpenAIEmbeddings
    # Get vectordb
    #persist_directory = 'information_db'
    persist_directory = 'combined_db'
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectordb = Chroma(persist_directory=persist_directory, 
                    embedding_function=embedding)
    
    #Setup retriever
    retriever = vectordb.as_retriever(search_kwargs={"k": 5,"score_threshold":0.65},search_type="similarity_score_threshold")#,score_threshold=0.2)#,verbose=True)

    #docs = retriever.get_relevant_documents(user_question)
    docs_and_scores = vectordb.similarity_search_with_score(user_question)
    docs=[]
    scores=[]
    for item in docs_and_scores:
        docs.append(item[0])
        scores.append(item[1])
    print(scores)

    open_website(docs[0])
    # if len(docs)==0:
    #     print("No documents found")
    # else:
    #     if "spreadsheet" in docs[0].metadata["mimeType"]:
    #         url = "https://docs.google.com/spreadsheets/d/"+docs[0].metadata["id"]
    #     elif "document" in docs[0].metadata["mimeType"]:
    #         url = "https://docs.google.com/document/d/"+docs[0].metadata["id"]
    #     elif "folder" in docs[0].metadata["mimeType"]:
    #         url = "https://drive.google.com/drive/folders/"+docs[0].metadata["id"]
    #     print(url)
    #     webbrowser.open(url)
    #print("Putting Docs in Queue",docs)
    return_que.put(docs)

def retrieve_from_folder(user_question):
    imports_done.wait()
    from langchain.vectorstores import Chroma
    from langchain.embeddings import OpenAIEmbeddings
    persist_directory = 'folder_db'
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectordb = Chroma(persist_directory=persist_directory, 
                    embedding_function=embedding)
    #Setup retriever
    retriever = vectordb.as_retriever(search_kwargs={"k": 6,"score_threshold":0.65},search_type="similarity_score_threshold")#,score_threshold=0.2)#,verbose=True)
    #docs = retriever.get_relevant_documents(user_question)

    docs_and_scores = vectordb.similarity_search_with_score(user_question)
    docs=[]
    scores=[]
    for item in docs_and_scores:
        docs.append(item[0])
        scores.append(item[1])
    print(scores)

    if len(docs)==0:
        print("No documents found")
    else:
        url = "https://drive.google.com/drive/folders/"+docs[0].metadata["id"]
        print(url)
        webbrowser.open(url)


def open_website(doc):
    if doc==None:
        print("No documents found")
    else:
        url=None
        if "spreadsheet" in doc.metadata["mimeType"]:
            url = "https://docs.google.com/spreadsheets/d/"+doc.metadata["id"]
        elif "document" in doc.metadata["mimeType"]:
            url = "https://docs.google.com/document/d/"+doc.metadata["id"]
        elif "folder" in doc.metadata["mimeType"]:
            url = "https://drive.google.com/drive/folders/"+doc.metadata["id"]
        print(url)
        if url != None:
            webbrowser.open(url)


















# if __name__=="__main__":
#     import openai
#     import os
#     with open("..\SECRET.txt",'r') as f:
#         OPENAI_SECRET=f.read().split("\n")[0]
#     os.environ['OPENAI_API_KEY'] = OPENAI_SECRET
#     openai.api_key=OPENAI_SECRET
#     information_dict_file_name="ainformation_dictionary.yaml"
#     with open(information_dict_file_name, "r") as file:
#             information_dict = yaml.load(file, Loader=yaml.FullLoader)
#     with open("afolder_dictionary.yaml", "r") as file:
#         folder_dictionary = yaml.load(file, Loader=yaml.FullLoader)
#     folder_dictionary=asyncio.run(a_update_folder_mapping(folder_dictionary,information_dict,override=True))
#     with open("afolder_dictionary.yaml", 'w') as outfile:
#         yaml.dump(folder_dictionary, outfile)










# if __name__=="__main__":
#     import openai
#     import os
#     with open("..\SECRET.txt",'r') as f:
#         OPENAI_SECRET=f.read().split("\n")[0]
#     os.environ['OPENAI_API_KEY'] = OPENAI_SECRET
#     openai.api_key=OPENAI_SECRET
#     combine_vectordb("combined_db")













# if __name__=="__main__":
#     from langchain.schema import (
#         AIMessage,
#         HumanMessage,
#         SystemMessage
#     )
#     import openai
#     import os
#     with open("..\SECRET.txt",'r') as f:
#         OPENAI_SECRET=f.read().split("\n")[0]
#     os.environ['OPENAI_API_KEY'] = OPENAI_SECRET
#     openai.api_key=OPENAI_SECRET
#     from langchain.chat_models import ChatOpenAI
#     import time
#     t_start=time.time()
#     chat=ChatOpenAI(model="gpt-3.5-turbo",temperature=0.3)
#     content_string="""Give me a 1 sentence description of this: "The learning environment for an expert must be stable and non random, have timely feedback, allow for many repetitions of a task, and the expert must practice deliberately. 
#     Valid environment
#     Non random space with patterns to learn
#     Timely feedback
#     Have to have quick feedback in order to map the inputs to the outputs and find patterns
#     Without quick feedback details are lost and the guesses will become more random
#     Repetition
#     Seeing or doing something 1 time is not sufficient to learn
#     Actively practicing and going through the patterns repeatedly is the only way to learn
#     Deliberate
#     Doing the same tasks you have always done does not make you better and you might forget some of the tasks you have done before but aren't doing anymore
#     Have to push yourself to do the things that are difficult and out of your comfort zone
#     Thousands of hours of practice

#     These ideas fit in line with my idea that your capacities now represent what you have been doing for the last several years of your life, more strongly represented by what you have done recently but the idea of accumulated functional capacity with exponential decay of acquired traits. "
# """
#     response=chat([HumanMessage(content=content_string)])
#     t_end=time.time()
#     print(t_end-t_start)
#     print(response)






















# if __name__=="__main__":
#     import together
#     import time
#     together_model_name="togethercomputer/llama-2-13b-chat"
#     together_model_name="togethercomputer/llama-2-7b-chat"
#     together_model_name="togethercomputer/llama-2-70b-chat"
#     together_model_name="togethercomputer/falcon-7b-instruct"
#     together.api_key = "cbed566397ee1f046d11392aa4400b2b11ae75de02655b8ebd95e110b2a26161"
#     model_list = together.Models.list()
#     for m in model_list:
#         if "display_type" in m.keys():
#             if m["display_type"]=="chat":
#                 print(m["name"])
#     content_string="""Give me a 3 word description of this: "The learning environment for an expert must be stable and non random, have timely feedback, allow for many repetitions of a task, and the expert must practice deliberately. 
#     Valid environment
#     Non random space with patterns to learn
#     Timely feedback
#     Have to have quick feedback in order to map the inputs to the outputs and find patterns
#     Without quick feedback details are lost and the guesses will become more random
#     Repetition
#     Seeing or doing something 1 time is not sufficient to learn
#     Actively practicing and going through the patterns repeatedly is the only way to learn
#     Deliberate
#     Doing the same tasks you have always done does not make you better and you might forget some of the tasks you have done before but aren't doing anymore
#     Have to push yourself to do the things that are difficult and out of your comfort zone
#     Thousands of hours of practice

#     These ideas fit in line with my idea that your capacities now represent what you have been doing for the last several years of your life, more strongly represented by what you have done recently but the idea of accumulated functional capacity with exponential decay of acquired traits." Start your 3 word description here:\n
# """ 
#     #please translate this
#     #content_string="Can dogs fly, yes or no?"
#     t_start=time.time()
#     together_output=together.Complete.create(
#         content_string,
#         model=together_model_name,
#         max_tokens=512,
#         temperature=0.7,
#         )
#     t_end=time.time()
#     print(t_end-t_start)
#     print(together_output["output"]["choices"][0]["text"])