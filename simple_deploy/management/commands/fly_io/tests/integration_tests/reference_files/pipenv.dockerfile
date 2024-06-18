ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIPENV_PIPFILE /tmp/Pipfile

RUN mkdir -p /code

WORKDIR /code

COPY Pipfile /tmp/Pipfile

RUN set -ex && \
    pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install && \
    rm -rf /root/.cache/

COPY . /code/

RUN ON_FLYIO_SETUP="1" pipenv run python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["pipenv", "run", "gunicorn", "--bind", ":8000", "--workers", "2", "blog.wsgi"]
