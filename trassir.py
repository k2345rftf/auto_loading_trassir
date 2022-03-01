import json
import requests as r
from datetime import datetime
import cv2
import os
from tqdm import tqdm

class Image:
    
    def __init__(self, path_to_image, mode='r'):
        self.path = path_to_image
        self.file = open(self.path, mode)
    
    def read(self):
        pass
    
    def write(self, data):
        self.file.write(data)
        
    def close(self):
        self.file.close()
        
    def __enter__(self):
        return self.file
    
    def __exit__(self, type, value, tb):
        self.close()

class Request:
    
    def __init__(self, ip, port, sid=''):
        self.ip = ip
        self.port = port
        
        self.session = sid
        
    def create_session(self, username, password):
        content_type, value = self.get(f'https://{self.ip}:{self.port}/login',params={'username':username, 'password':password})
        self.session = value['sid']
        
        
    def _json_deserialize(self, json_text) -> dict:
        return json.loads(json_text[:json_text.index('/*')] if json_text.find('/*')>-1 else json_text)
        
    def get(self, url, params:dict={}):
        if self.session != '':
            params['sid'] = self.session
        response = r.get(url, params=params, verify=False)
        value = self._json_deserialize(response.text) if response.headers['Content-Type'].startswith('application/json') else response.content   
        return response, value


class Camera:
    
    def __init__(self, server, guid, name):
        self._request = server
        self._guid = guid
        a = ':\\/*?<>|"'
        self.name = name
        for char in a:
            self.name = self.name.replace(char, '-')
        
    def _save_image(self, path, img):
            
        with Image(f'{path}.jpeg', 'wb') as f:
            f.write(img)
        
    
    def load_screenshot(self, path: str, timestamp):
        print(path)
        response, img = self._request.get(f'https://{self._request.ip}:{self._request.port}/screenshot/{self._guid}', params={'timestamp': str(timestamp)})
        if not response.headers['Content-Type'].startswith('image/jpeg'):
            print(f'Изображение с камеры {self._guid} по таймкоду {timestamp} не удалось загрузить')
            return
            
        self._save_image(path+'_'+str(timestamp), img)

        
    def load_video(self, dt_start, dt_end):
        dt_s = int(dt_start.timestamp())
        dt_e = int(dt_end.timestamp())
        if not os.path.isdir('data'):
            os.mkdir('data')

        path = f'data/{self._guid}_{self.name}_{dt_s}_{dt_e}'.replace(':', '-')

        for i in range(dt_e-dt_s):
            timestamp = dt_s + i                  
            self.load_screenshot(path, timestamp)
        
        
class RemoteTrassirArchive:
    
    def __init__(self, ip, port, username, password, mock=False):
        self.url = f'https://{ip}:{port}'
        self._server = Request(ip, port)
        self._server.create_session(username, password)
        self.camers={}
        
        response, channels = self._server.get(self.url+'/channels')
        
        self.camers = {}
        
        for channel in channels['channels']:
            self.camers[channel['name']] = Camera(self._server, channel['guid'], channel['name'])

        
    def load_screenshots(self, operations):
        for cam_name, dt_s, dt_e in operations:
            print(cam_name in self.camers.keys())
            if cam_name in self.camers:
                self.camers[cam_name].load_video(dt_s, dt_e)
