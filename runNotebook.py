import io
import base64
import binascii
import json
import requests
import datetime
import uuid
from pprint import pprint
from websocket import create_connection
from PIL import Image 
Image.MAX_IMAGE_PIXELS = None

print('runPy...');
# The token is written on stdout when you start the notebook
#notebook_path = '/pyAFDC.ipynb'
notebook_path = '/Edge_Detection.ipynb'
#notebook_path = '/pyJupyter/notebook/Edge_Detection.ipynb'
# notebook_path = '/demo_notebooks/preProcessing.ipynb'
base = 'http://localhost:8888'
# headers = {'Authorization': 'Token 207bad23989b4b70984c93fcba03c1e87c79fbc6954bc465'}:
headers = {'Authorization': 'Token <generated>'}
# notebook_path = '/test.ipynb'
# base = 'https://jupyter.asdc.cloud.edu.au:8888/user/chris.peters@csiro.au'
# headers={'Authorization': 'Token 4a2b174060ef441d92675db6e51c6ec0'}
# headers={'Authorization': 'Token 77fe241dcb764f1fae1f30020073e405'}

import os
cwd = os.getcwd()
print("Current working directory: {0}".format(cwd))

url = base + '/api/kernels'
# url = base

response = requests.post(url,headers=headers)
print('response=',response);
kernel = json.loads(response.text)

# Load the notebook and get the code of each cell
url = base + '/api/contents' + notebook_path
#url = base + '/api' + notebook_path
#url = base + '/notebooks' + notebook_path
#print('url=',url);
response = requests.get(url,headers=headers)
print('response=',response);
#print('response.text=',response.text);
file = json.loads(response.text)
#print('file=',file);
code = [ c['source'] for c in file['content']['cells'] if len(c['source'])>0 ]
#print('code=',code)

# Execution request/reply is done on websockets channels
ws = create_connection("ws://localhost:8888/api/kernels/"+kernel["id"]+"/channels",
     header=headers)

def send_execute_request(code):
    msg_type = 'execute_request';
    content = { 'code' : code, 'silent':False }
    id = uuid.uuid1().hex
    print('id=',id)
    hdr = { 'msg_id' : id, 
        'username': 'test', 
        'session': uuid.uuid1().hex, 
        'data': datetime.datetime.now().isoformat(),
        'msg_type': msg_type,
        'version' : '5.0' }
    msg = { 'header': hdr, 'parent_header': hdr, 
        'metadata': {},
        'content': content }
    print(msg)
    return msg

for c in code:
    # print('c=',c)
    ws.send(json.dumps(send_execute_request(c)))

state_count=0
exit=False
# We ignore all the other messages, we just get the code execution output
# (this needs to be improved for production to take into account errors, large cell output, images, etc.)
# for i in range(0, len(code)):
while 1:
    msg_type = '';
    while msg_type != "stream":
        rsp = json.loads(ws.recv())
        parent_msg_id = rsp['parent_header']['msg_id']
        print('parent_msg_id=',parent_msg_id)
        #print('rsp=',rsp)
        msg_type = rsp["msg_type"]
        print('msg-type=',msg_type)

        if msg_type =="display_data":
           print('image found')
           fmt=rsp["content"]["data"]["text/plain"]
           img=rsp["content"]["data"]["image/png"]
           print('fmt=',fmt,', img=',img[:50],'......',img[-50:])

           f = open("fracture.png", "wb")
           #f.write(binascii.unhexlify(img.strip()))
           f.write(base64.b64decode(img.strip()))
           f.close()

           #img = Image.open('test.png')
           #base64.b64decode(img.strip()).show() 
           #imgF = Image.open('fracture.png')
           #imgF.show() 
           #imgStr = base64.b64decode(img.strip())
           f = io.BytesIO(base64.b64decode(img.strip()))
           pilImage = Image.open(f)
           pilImage.show()
           now = datetime.datetime.now() # current date and time
           date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
           print('['+date_time+']show image')

           #i=Image(imgStr)
           #i.show()

        if msg_type == "status":
           state_count=state_count+1
           execution_state = rsp["content"]["execution_state"]
           print('execution_state.1=',execution_state,state_count)
           if execution_state =="idle" and state_count > 2:
              print('break')
              exit = True
              break

    if exit:
       break
    now = datetime.datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    print('['+date_time+']'+rsp["content"]["text"])
    if msg_type == "status":
        execution_state = rsp["content"]["execution_state"]
        print('execution_state.2=',execution_state,state_count)
        if execution_state == "idle":
            print('break')
            break

ws.close()
