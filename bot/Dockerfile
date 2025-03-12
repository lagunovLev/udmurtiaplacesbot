FROM python:latest

WORKDIR /bot
ENV PYTHONPATH="${PYTHONPATH}:/"
ENV DEPLOYING=True
RUN pip install --upgrade pip
COPY ./requirements.txt /bot/requirements.txt
RUN pip install -r requirements.txt
COPY . /bot

EXPOSE 8080
CMD ["python", "__init__.py"]