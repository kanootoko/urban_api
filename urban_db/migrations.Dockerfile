FROM python:3.11-alpine

RUN apk add --virtual build-deps
RUN apk add python3-dev musl-dev linux-headers postgresql-dev geos-dev

RUN pip3 install --no-cache-dir poetry

COPY pyproject.toml /app/pyproject.toml
RUN sed -i '0,/version = .*/ s//version = "0.1.0"/' /app/pyproject.toml && touch /app/README.md

WORKDIR /app
RUN poetry config virtualenvs.create false
RUN poetry install --with dev

COPY README.md /app/README.md
COPY urban_db /app/urban_db


RUN echo "cd /app/urban_db" > /entrypoint.sh && \
    echo "poetry run alembic upgrade head" >> /entrypoint.sh && \
    echo 'if [ $? = 0 ]; then echo "Database schema syncronized"; else echo "alembic upgrade has failed, database state is not determined"; exit 1; fi' >> /entrypoint.sh

RUN pip3 install .

ENTRYPOINT ["/bin/sh"]
CMD ["/entrypoint.sh"]
