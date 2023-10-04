import time
if __name__=="__main__":
    t_s_abs=time.time()

# tkinter imports
import threading
import tkinter as tk
from tkinter import StringVar, Entry, Label, Button
import queue


# Custom modules imports
import sys
sys.path.append('smartdrivefunctions')
from deferred_imports import load_slow_imports

# Start slow imports in background
threading.Thread(target=load_slow_imports).start()

import dictionary_functions as adf
import smart_functions as asf



# Sound recording
from pvrecorder import PvRecorder
import wave, struct 
import time
import numpy as np


# Define paths
dictionaries_folder_path="dictionaries"
structure_dictionary_path=dictionaries_folder_path+"/structure_dictionary.yaml"
information_dictionary_path=dictionaries_folder_path+"/information_dictionary.yaml"
folder_dictionary_path=dictionaries_folder_path+"/folder_dictionary.yaml"

# Update paths in dictionary_functions
adf.dictionaries_folder_path=dictionaries_folder_path
adf.structure_dictionary_path=structure_dictionary_path
adf.information_dictionary_path=information_dictionary_path
adf.folder_dictionary_path=folder_dictionary_path

# Update paths in smart_functions
asf.dictionaries_folder_path=dictionaries_folder_path
asf.structure_dictionary_path=structure_dictionary_path
asf.information_dictionary_path=information_dictionary_path
asf.folder_dictionary_path=folder_dictionary_path


#Openai imports and key
import openai
import os
with open("SECRET.txt",'r') as f:
    OPENAI_SECRET=f.read().split("\n")[0]
os.environ['OPENAI_API_KEY'] = OPENAI_SECRET
openai.api_key=OPENAI_SECRET
model_name="gpt-3.5-turbo"


#Drive imports
import asyncio
import pickle
from concurrent.futures import ThreadPoolExecutor
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow




#Main Tkinter App
class App:
    def __init__(self, root, q):
        # INITIALIZATION
        self.root = root
        self.q = q
        self.root.title("Smart Drive App")
        self.root.geometry("500x800")
        self.docs_list=[]
        self.doc_index=1
        self.start_recording_thread=False
        self.vector_update_statuses=[False,False]



        # Entry to get user input
        self.entry = Entry(self.root)
        self.entry.pack(pady=20)

        #Shows you when you are recording
        def change_dot_color(self):
            self.recording_dot["fg"]="red"
            self.start_recording_thread=True
        
        # Rotates the retrieved docs
        def rotate_options(self):
            if len(self.docs_list)!=0:
                self.doc_index%=len(self.docs_list)
                asf.open_website(self.docs_list[self.doc_index])
                self.doc_index+=1



        # ACTIONS
        # Button to record and retrieve
        self.btn_start_recording = Button(root, text="Record Retrieve Info",command=lambda: change_dot_color(self))
        self.btn_start_recording.pack(pady=10)

        # Button to record and retrieve from folders
        self.btn_start_recording = Button(root, text="Record Retrieve Folder", command=lambda: self.start_thread("record_retrieve_folder"))
        self.btn_start_recording.pack(pady=10)

        # Button to retrieve from drive
        self.btn_start = Button(root, text="Retrieve from Drive", command=lambda: self.start_thread("retrieve_information"))
        self.btn_start.pack(pady=10)

        # Index through options
        self.btn_rotate = Button(root, text="Rotate through options", command=lambda: rotate_options(self))
        self.btn_rotate.pack(pady=10)



        # UPDATES
        # Button to toggle accessibility to update buttons
        self.btn_toggle = Button(root, text="Toggle Accessibility", command=lambda: self.toggle_accessibility())
        self.btn_toggle.pack(pady=30)

        # Button to update structure toggled off by default
        self.btn_struct_update = Button(root, text="Update Structure", command=lambda: self.start_thread("update_structure"))
        self.btn_struct_update.pack(pady=10)
        self.btn_struct_update["state"]="disabled"
        self.btn_struct_update["text"]="Update Structure (Disabled)"

        # Button to update information toggled off by default
        self.btn_info_update = Button(root, text="Update Information", command=lambda: self.start_thread("update_information"))
        self.btn_info_update.pack(pady=10)
        self.btn_info_update["state"]="disabled"
        self.btn_info_update["text"]="Update Information (Disabled)"

        # Button to update mapping toggled off by default
        self.btn_map_update = Button(root, text="Update Mapping", command=lambda: self.start_thread("update_mapping"))
        self.btn_map_update.pack(pady=10)
        self.btn_map_update["state"]="disabled"
        self.btn_map_update["text"]="Update Mapping (Disabled)"

        # Button to update vectordb toggled off by default and faded out
        self.btn_vdb_update = Button(root, text="Update VectorDB", command=lambda: self.start_thread("update_vectordb"))
        self.btn_vdb_update.pack(pady=10)
        self.btn_vdb_update["state"]="disabled" 
        self.btn_vdb_update["text"]="Update VectorDB (Disabled)"

        # Button to update everything toggled off by default
        self.btn_everything_update = Button(root, text="Update Everything", command=lambda: self.start_thread("update_everything"))
        self.btn_everything_update.pack(pady=10)
        self.btn_everything_update["state"]="disabled"
        self.btn_everything_update["text"]="Update Everything (Disabled)"



        # Displays
        # Label to display the result
        self.result_var = StringVar()
        self.result_var.set("Result will be displayed here...")
        self.label = Label(root, textvariable=self.result_var)
        self.label.pack(pady=10)

        # Make large red dot while recording
        color_dark_red="#690000"
        self.recording_dot=Label(root, text="●", fg=color_dark_red, font=("Helvetica", 100))
        self.recording_dot.pack(side="bottom", anchor="se")



        # Get boot time
        global t_s_abs
        print("Time to initialize: ",time.time()-t_s_abs)

        # Queue for the background thread
        self.root.after(100, self.check_queue())

    def check_queue(self):
        # Make large red dot while recording
        if self.start_recording_thread==True:
            self.start_recording_thread=False
            self.start_thread("record_retrieve_information")
        
        # Check if there is a result from the background thread
        if hasattr(self, 'return_que'):
            try:
                result_list = self.return_que.get(0)
                self.docs_list=result_list
                delattr(self, 'return_que') 
            except queue.Empty:
                #print("Result queue is empty.")
                pass

        # If no result yet, continue checking
        self.root.after(100, self.check_queue)


    def toggle_accessibility(self):
        #Toggle the update dictionary and update vectordb buttons
        def flip_toggle(button):
            if button["state"]=="disabled":
                button["state"]="normal"
                button["text"]=button["text"].replace("Disabled","Enabled")
            else:
                button["state"]="disabled"
                button["text"]=button["text"].replace("Enabled","Disabled")
        flip_toggle(self.btn_struct_update)
        flip_toggle(self.btn_info_update)
        flip_toggle(self.btn_map_update)
        flip_toggle(self.btn_vdb_update)
        flip_toggle(self.btn_everything_update)

    def start_thread(self,process_name):
        user_input = self.entry.get()

        # ACTIONS
        if process_name=="retrieve_information":
            return_que=queue.Queue()
            threading.Thread(target=asf.retrieve_from_information,args=(user_input,return_que,)).start()
            self.q.put(return_que)
        elif process_name=="record_retrieve_information":
            self.doc_index=1
            return_que_record=queue.Queue()
            rt=threading.Thread(target=record_audio, args=(return_que_record,))
            rt.start()
            rt.join()
            result_from_thread = return_que_record.get()
            self.recording_dot["fg"]="#690000"
            self.result_var.set(f"Processed Result: {result_from_thread}")
            self.return_que=queue.Queue()
            threading.Thread(target=asf.retrieve_from_information,args=(result_from_thread,self.return_que,)).start()
        elif process_name=="record_retrieve_folder":
            rt=threading.Thread(target=record_audio, args=(return_que,))
            rt.start()
            rt.join()
            result_from_thread = return_que.get()
            self.result_var.set(f"Processed Result: {result_from_thread}")
            threading.Thread(target=asf.retrieve_from_folder,args=(result_from_thread,)).start()
        


        # UPDATES
        elif process_name=="update_structure":
            threading.Thread(target=call_asyn_dict_updates,args=("structure",)).start()
        elif process_name=="update_information":
            threading.Thread(target=call_asyn_dict_updates,args=("information",)).start()
        elif process_name=="update_mapping":
            threading.Thread(target=asf.map).start()
        elif process_name=="update_vectordb":
            threading.Thread(target=asf.update_vectordb,args=("information_db")).start()
            threading.Thread(target=asf.update_vectordb,args=("folder_db")).start()
            threading.Thread(target=asf.combine_vectordb,args=("combined_db",)).start()
        elif process_name=="update_everything":
            threading.Thread(target=update_everything_function).start()




# Record audio
def record_audio(return_queue):
    recorder = PvRecorder(device_index=0, frame_length=512)
    audio = []
    path = 'audio_recording.wav'
    avg_loudness=0
    t_start=time.time()
    tlt_100=time.time()
    try:
        # Start recording
        recorder.start()
        print("Starting Recording")
        while True:
            # Get audio frame
            frame = recorder.read()
            audio.extend(frame)

            # Calculate average loudness
            avg_loudness+=np.mean(np.abs(frame))*0.3
            avg_loudness*=0.7
            print("Average Loudness: ", avg_loudness,"     ", end='\r')

            # If the average loudness is below 120 for 0.35 seconds after 1 second, stop recording
            if (time.time()-t_start)>1.0:
                if avg_loudness<120:
                    if (time.time()-tlt_100)>0.35:
                        raise KeyboardInterrupt
                else:
                    tlt_100=time.time()
            else:
                tlt_100=time.time()
    except KeyboardInterrupt:
        # Stop recording and save to file
        recorder.stop()
        with wave.open(path, 'w') as f:
            f.setparams((1, 2, 16000, 512, "NONE", "NONE"))
            f.writeframes(struct.pack("h" * len(audio), *audio))
        recorder.delete()
        print("Recording Finished")
    finally:
        # Transcribe audio
        t_start=time.time()
        audio_file= open(path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        t_end=time.time()
        print("Time to transcribe: ",t_end-t_start, " Text:",transcript["text"])

        # Return transcript to main thread to display and for functions
        return_queue.put(transcript["text"])
        return(transcript["text"])




# Update dictionaries
def call_asyn_dict_updates(select_string):
    #Get creds
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    secret_path="sgd_secret.json"
    if not creds or not creds.valid or creds.expired:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/documents.readonly']
        try:
            creds.refresh(Request())
        except:
            flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    #Update dictionaries with 'structure' and 'information'
    asyncio.run(adf.main(creds, select_string))




# Update everything
def update_everything_function():
    call_asyn_dict_updates("structure")
    call_asyn_dict_updates("information")
    asf.map()
    asf.combine_vectordb("combined_db")
    print("Finished updating everything")







# Main
if __name__ == "__main__":
    executor = ThreadPoolExecutor(max_workers=5)
    root = tk.Tk()
    q = queue.Queue()
    app = App(root, q)
    root.mainloop()