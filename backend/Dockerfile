FROM python:3.12.3

WORKDIR /backend

COPY /backend/requirements.txt ./

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
