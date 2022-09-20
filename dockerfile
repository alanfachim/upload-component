FROM alpine:latest
LABEL maintainer="stuart@newlymintedmedia.com"
 

RUN apk update && apk add python3 py3-pip libreoffice
RUN apk add --no-cache msttcorefonts-installer fontconfig
ENV URLOVERRIDE="http://ms-fonts-libreoffice.s3.sa-east-1.amazonaws.com/"
RUN update-ms-fonts

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5027

CMD [ "python3", "./main.py" ]
 



 