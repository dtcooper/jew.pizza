FROM python:3.9

EXPOSE 8000/tcp

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.1.8

RUN wget -qO /usr/local/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/81b1373f/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

RUN mkdir /app
WORKDIR /app
COPY jew_pizza/pyproject.toml jew_pizza/poetry.lock /app/
RUN poetry install

COPY entrypoint.sh /
COPY jew_pizza/ /app/

ENTRYPOINT ["/entrypoint.sh"]
CMD []
