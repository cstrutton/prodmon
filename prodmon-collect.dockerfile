from python:3.8-slim

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY . .
RUN pip install -e .

# using ENTRYPOINT means that options on the docker run command will be passed to the running command
CMD "/usr/bin/python ./prodmon/plc_collect/main.py ${CONFIG}"
