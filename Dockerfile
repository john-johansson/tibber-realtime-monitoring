FROM python:3.8-slim-buster
WORKDIR /realtime
COPY requirements.txt requirements.txt
COPY realtime/realTime.py realTime.py
RUN pip3 install -r requirements.txt
RUN rm -f requirements.txt
CMD [ "python3", "realTime.py" ]

