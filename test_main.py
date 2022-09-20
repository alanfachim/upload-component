from datetime import datetime
import os
import unittest
from unittest.mock import MagicMock, Mock, patch
from flask import Flask, json, request, Response

os.environ["prefix"]="/v1/analise"
os.environ["queue_url"]="https://sqs.sa-east-1.amazonaws.com/469122751664/generate-thumbnail"
os.environ["bucket_name"] ='fachim-test'
from controller import Controller 

class MockS3():
    def list_objects(self,**kwparams):
        return {"Contents":[{"Key":"teste/teste.exe"}]}
    def generate_presigned_url(self,type,**kwparams):
        return "https://teste.com/"
    def head_object(self,**kwparams):
        return {"LastModified":datetime.now(), "ContentLength":10, "ResponseMetadata":{"HTTPHeaders":{"x-amz-meta-num-funl-colb":"12345679", "x-amz-meta-cod-classificacao":"01"}}}
    def delete_object(self,**kwparams):
        return "ok"
        
class test_TestStringMethods(unittest.TestCase):
 
         

    @patch('controller.Controller.__init__', return_value=None)
    @patch('controller.Controller.s3', MockS3())
    def test_get_files(self, mock): 
        self.api = Flask(__name__) 
        Controller.register(self.api, route_base = '/')  
        tester=self.api.test_client(self)
        response = tester.get('/v1/analise/1234-123-41-2341234-12341234-234/arquivos') 
        self.assertEqual(response.status_code, 200)

    @patch('controller.Controller.__init__', return_value=None)
    @patch('controller.Controller.s3', MockS3())
    def test_post_files(self, mock): 
        self.api = Flask(__name__) 
        Controller.register(self.api, route_base = '/')  
        tester=self.api.test_client(self)
        response = tester.post('/v1/analise/1234-123-41-2341234-12341234-234/arquivos', content_type='application/json', data='{"data":[{"nome":"teste.txt", "num-funl-colb":"123456789","cod-classificacao":"01","content-length":123}]}') 
        self.assertEqual(response.status_code, 200)

    @patch('controller.Controller.__init__', return_value=None)
    @patch('controller.Controller.s3', MockS3())
    def test_delet_files(self, mock): 
        self.api = Flask(__name__) 
        Controller.register(self.api, route_base = '/')  
        tester=self.api.test_client(self)
        response = tester.delete('/v1/analise/1234-123-41-2341234-12341234-234/arquivos/teste.txt') 
        self.assertEqual(response.status_code, 200)

    @patch('controller.Controller.__init__', return_value=None)
    @patch('controller.Controller.s3', MockS3())
    def test_delet_files(self, mock): 
        self.api = Flask(__name__) 
        Controller.register(self.api, route_base = '/')  
        tester=self.api.test_client(self)
        response = tester.delete('/v1/analise/1234-123-41-2341234-12341234-234/arquivos/teste.txt') 
        self.assertEqual(response.status_code, 200)
 

if __name__ == '__main__':
    unittest.main()