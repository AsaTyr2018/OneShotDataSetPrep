FROM python:3.12-slim

# set working directory
WORKDIR /app

# install dependencies first
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy application code
COPY . .

# create directory for generated archives
RUN mkdir -p /app/archives

EXPOSE 7860

CMD ["python", "run.py"]
