FROM pypy:3.7-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates gcc \
    libxml2 libxml2-dev libxslt1-dev zlib1g-dev \
    fonts-liberation fonts-noto-cjk \
    wkhtmltopdf \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV APP_DIR /app

WORKDIR ${APP_DIR}

COPY Pipfile Pipfile.lock ${APP_DIR}/

RUN pip install pipenv --no-cache-dir && \
    pipenv install --system --deploy && \
    pip uninstall -y pipenv virtualenv-clone virtualenv && \
    mkdir ${APP_DIR}/downloads

COPY . ${APP_DIR}/

ENV PDFC_MODE "new"
ENV PDFC_ALLOW_LOCAL_BACKUP false
ENV PDFC_PDF_FORMAT "pass-through"
ENV PDFC_USE_HISTORY true
ENV PDFC_STORAGE "dropbox"
ENV PDFC_CLOUD_TOKEN ""
ENV PDFC_MK_ID ""
ENV PDFC_MK_PW ""

CMD ["pypy3", "-c", "from concierge import app; app.execute();"]