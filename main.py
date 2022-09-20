
import os
import threading
from flask import Flask, json, request, Response
from flask_cors import CORS, cross_origin 
from botocore.errorfactory import ClientError

os.environ["prefix"]="/v1/analise"
os.environ["queue_url"]="https://sqs.sa-east-1.amazonaws.com/469122751664/generate-thumbnail"
os.environ["bucket_name"] ='fachim-test'
from controller import Controller
  

if __name__ == '__main__':
    api = Flask(__name__)
    cors = CORS(api)
    Controller.register(api, route_base = '/') 
    controller = Controller()
    threading.Thread(target=lambda: api.run( host='0.0.0.0', port=8080, debug=True, use_reloader=False)).start()
    print("listening events")
    #long_pulling()
        
        