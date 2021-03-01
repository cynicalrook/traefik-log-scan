FROM python:3.9-slim-buster
WORKDIR /app
COPY traefiklogscan.py /app/
COPY config.ini.sample /app/
COPY exclude-ips.txt.sample /app/
COPY requirements.txt /app/
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
CMD [ "traefiklogscan.py" ]
EXPOSE 8050
