#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery import MediaFileUpload
from apiclient.http import MediaIoBaseDownload
import json
import os
import io

class GDrive():
    def __init__(self):
        credfile = "creds.json"
        self.writeCredsJSON(credfile)
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.SERVICE_ACCOUNT_FILE = credfile
        self.credentials = service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
        self.cleanJSON(credfile)
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.folderid = os.environ["GDRIVE_FOLDERID"]
        self.historicfolder = os.environ["GDRIVE_BACKUP_FOLDER"]
        self.homeFolder = {
                "kind" : "drive#file",
                "id" : self.folderid, 
                "name":"Heroku Files",
                'mimeType': 'application/vnd.google-apps.folder'
                }
        
    def writeCredsJSON(self,filename):
        with open(filename,"r") as f:
            data = json.load(f)
        data["project_id"] = os.environ['GDRIVE_PROJ_ID']
        data["private_key_id"] = os.environ["GDRIVE_PRIVKEY_ID"]
        data["private_key"] = os.environ["GDRIVE_PRIVKEY"]
        data["client_email"] = os.environ["GDRIVE_CLIENT_EMAIL"]
        data["client_id"] = os.environ["GDRIVE_CLIENT_ID"]
        data["client_x509_cert_url"] = os.environ["GDRIVE_CERT_URL"]
        with open(filename, 'w') as f:
            json.dump(data, f)
    
    def cleanJSON(self,filename):
        with open(filename,"r") as f:
            data = json.load(f)
        data["project_id"] = ""
        data["private_key_id"] = ""
        data["private_key"] = ""
        data["client_email"] = ""
        data["client_id"] = ""
        data["client_x509_cert_url"] = ""
        with open(filename, 'w') as f:
            json.dump(data, f)
            
    def write_file(self,data,filename):
        with open(filename,"wb") as f:
            f.write(data)
    
    def download_files(self):
        files = self.list_files()
        fh_list = []
        for file in files["files"]:
            if(file["mimeType"] != "application/vnd.google-apps.folder"):
                file_id = file["id"]              
                request = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print("Download {} %d%%.".format(file["name"]) % int(status.progress() * 100))
                self.write_file(fh.getvalue(),file["name"])
                fh_list.append([fh,status,downloader])
        return fh_list
    
    def trashFile(self,file_id):
        body = {'trashed': True}
        updated_file = self.service.files().update(fileId=file_id, body=body).execute()
        return updated_file
    
    def backupFile(self,file_id):
        folder_id = self.historicfolder
        # Retrieve the existing parents to remove
        file = self.service.files().get(fileId=file_id,
                                         fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        # Move the file to the new folder
        file = self.service.files().update(fileId=file_id,
                                            addParents=folder_id,
                                            removeParents=previous_parents,
                                            fields='id, parents').execute()

    
    def upload_files(self,filenames):
        all_files = self.list_files()
        for file in all_files["files"]:
            if(file["mimeType"] != "application/vnd.google-apps.folder"):
                self.backupFile(file["id"])
        
        for filename in filenames:
            file_metadata = {
                "name": filename,
                'mimeType': 'text/csv',
                "parents" : [self.folderid]
                }
            media = MediaFileUpload(filename,
                                    mimetype='text/csv',
                                    resumable=True)
            file = self.service.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id').execute()
            
    def list_files(self):
        query = "'{}' in parents".format(self.homeFolder['id'])
        filesInFolder = self.service.files().list(q=query, orderBy='folder', pageSize=10).execute()
        return filesInFolder 
