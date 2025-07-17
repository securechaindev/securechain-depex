FROM python:3.13.2-slim

WORKDIR /

COPY /requirements.txt ./

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "app", "--reload-exclude", "repositories"]