import boto3
import json
import urllib
import os
import base64
from flask import Flask, json, request, Response
from flask_classful import FlaskView, route
from flask_cors import CORS, cross_origin
import threading
from PIL import Image
import PIL
import glob
import shutil
from botocore.errorfactory import ClientError


class Controller(FlaskView):
    s3 = None
    queue_url = os.environ["queue_url"]
    bucket_name = os.environ["bucket_name"]
    prefix = os.environ["prefix"]

    def __init__(self):
        self.session = boto3.Session(region_name='sa-east-1')

        # Create SQS client
        self.sqs = self.session.client('sqs')
        self.s3 = self.session.client(
            's3', config=boto3.session.Config(signature_version='s3v4'))

    @route('/actuator/health', methods=['GET'])
    @cross_origin()
    def get_health(self):
        return 'ok'

    @route(f'{os.environ["prefix"]}/<subfolder>/arquivos', methods=['GET'])
    @cross_origin()
    def get_files(self, subfolder):
        response = []
        show_all = request.args.get("all")
        for key in self.s3.list_objects(Bucket=self.bucket_name, Prefix=f'images/{subfolder}/')["Contents"]:
            try:
                name = key["Key"].split("/")
                name = name[len(name) - 1]
                if len(name) > 2:
                    url = self.s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": self.bucket_name, "Key": key["Key"]},
                        ExpiresIn=300,
                    )
                    info = self.s3.head_object(
                        Bucket=self.bucket_name, Key=key["Key"])
                    response.append(
                        {
                            "name": name,
                            "url": url,
                            "last-modified": info["LastModified"].strftime(
                                "%Y-%m-%dT%H:%M:%S"
                            ),
                            "content-length": info["ContentLength"],
                            "num-funl-colb": info["ResponseMetadata"]["HTTPHeaders"][
                                "x-amz-meta-num-funl-colb"
                            ],
                            "cod-classificacao": info["ResponseMetadata"]["HTTPHeaders"][
                                "x-amz-meta-cod-classificacao"
                            ],
                            "thumbnail-base-64": self.get_thumbnail(name, key["Key"], show_all),
                        }
                    )
            except:
                print(json.dumps(key))
        return json.dumps(response)

    @route(f'{os.environ["prefix"] }/<subfolder>/arquivos', methods=['POST'])
    @cross_origin()
    def post_files(self, subfolder):
        result = []
        for file in request.get_json()["data"]:
            if file["content-length"] > 50000000:
                return Response("{'message':'Arquivo tem o tamanho maior do que o permitido'}", status=400, mimetype='application/json')
            else:
                result.append([
                    {
                        "url": self.s3.generate_presigned_url(
                            "put_object",
                            Params={
                                "Bucket": self.bucket_name,
                                "Key": f"images/{subfolder}/{file['nome']}",
                                "ContentLength": file["content-length"],
                                "Metadata": {
                                    "num-funl-colb": file["num-funl-colb"],
                                    "cod-classificacao": file["cod-classificacao"],
                                },
                            },
                            ExpiresIn=100,
                        ),
                        "nome": file['nome'],
                        "content-length": file['content-length'],
                        "x-amz-meta-num-funl-colb":file['nome'],
                        "x-amz-meta-cod-classificacao":file['nome']
                    }
                ])
        return json.dumps({"data": result})

    @route(f'{os.environ["prefix"]}/<subfolder>/arquivos/<nome>', methods=['DELETE'])
    @cross_origin()
    def delete_file(self, subfolder, nome):
        self.s3.delete_object(Bucket=self.bucket_name,
                              Key=f'imagem/{subfolder}/{nome}')
        return f'{{ "message": "arquivo {nome} deletado"}}'

    def get_thumbnail(self, filename, key, all):
        print('thumbnail/'+key)
        ext = filename.split('.')[-1]
        prefix = f'data:image/{ext};base64,'
        try:
            obj = self.s3.get_object(
                Bucket=self.bucket_name, Key=f'thumbnail/{key}.png')
            return prefix + base64.b64encode(obj['Body'].read()).decode('utf-8')
        except ClientError:
            if all == '1':
                with open(filename, 'rb') as f:
                    img = f.read()
                return prefix + base64.b64encode(img).decode('utf-8')
            else:
                print("miniatura não encontrada")
                raise Exception("miniatura não encontrada")

    def convert_files(self, filename):
        ext = filename.split('.')[-1]
        if ext in ['docx', 'doc', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'pdf', 'xml', 'json', 'csv']:
            os.system(f'libreoffice --headless --convert-to png "{filename}"')
            self.resize(filename.replace('.'+ext, '.png'))
        elif ext in ['jpeg', 'png', 'tiff', 'tif', 'bmp', 'jpg', 'gif', 'pdf']:
            self.resize(filename)
        elif ext in ['zip', '7z', 'rar']:
            shutil.copyfile('zip.png', filename)
            self.resize(filename)
        else:
            shutil.copyfile('generic.png', filename)
            self.resize(filename)
        return filename.replace(f'.{ext}', '.png')

    def resize(self, filename):
        base_width = 250
        image = Image.open(filename)
        width_percent = (base_width / float(image.size[0]))
        hsize = int((float(image.size[1]) * float(width_percent)))
        image = image.resize((base_width, hsize), PIL.Image.ANTIALIAS)
        ext = filename.split('.')[-1]
        return image.save(filename.replace('.'+ext, '.png'))

    def image_to_data_url(self, filename):
        ext = filename.split('.')[-1]
        prefix = f'data:image/{ext};base64,'
        with open(filename, 'rb') as f:
            img = f.read()
        return prefix + base64.b64encode(img).decode('utf-8')

    def long_pulling(self):
        while True:
            # Receive message from SQS queue
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                AttributeNames=[
                    'SentTimestamp'
                ],
                MaxNumberOfMessages=10,
                MessageAttributeNames=['All'],
                VisibilityTimeout=5,
                WaitTimeSeconds=20
            )
            if 'Messages' in response:
                message = response['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                # downlod file
                name = ''
                try:
                    print(message['Body'])
                    body = json.loads(message['Body'])['Records'][0]
                    bucket = body['s3']['bucket']['name']
                    key = urllib.parse.unquote(
                        body['s3']['object']['key']).replace('+', ' ')
                    name = key.split('/')
                    name = name[len(name)-1]
                    print('Received and deleted message: %s %s',
                          key, body['s3']['bucket']['name'])
                    ext = name.split('.')[len(name.split('.'))-1]
                    clear = ''
                    if ext.lower() in ['json', 'ts', 'cs']:
                        name = f'{name}.txt'
                        clear = '.txt'
                    self.s3.download_file(bucket, key, name)
                    pdf_file_path = self.convert_files(name)
                    name = name.replace(clear, '')
                    print('Preview created at path : ', pdf_file_path)
                    self.s3.upload_file(
                        pdf_file_path, bucket, f'thumbnail/{key}.png')
                    os.remove(pdf_file_path)
                    os.remove(name)
                except:
                    print(f"erro ap processar o arquivo: {name}")

                # Delete received message from queue
                self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
