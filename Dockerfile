# This is will be the host os for your container
FROM python:3.9.6-buster

# This is will be just some information about the author
LABEL maintainer="Izhar Hussain <ixxhar@gmail.com>"

# This is will be the open port for the container
EXPOSE 5000/tcp

# This is will be the directory inside the container holding our project
WORKDIR /app

# This is will copy the requirements.txt file to app directory
COPY requirements.txt .

# This is will be used for installing all the python libraries
RUN pip install -r requirements.txt

# This is will copy all the files and folder of our root to the app directory
COPY . .

# This is will be our project starting point
# ENV FLASK_APP=index.py

# This is will be used for determining that we are using flask with python3 and execute the index.py when container is runned.
# CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]