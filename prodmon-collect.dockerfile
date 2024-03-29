from python:3.8-slim

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

COPY bin bin

# copy the content of the local src directory to the working directory
COPY prodmon prodmon

COPY setup.py setup.py
RUN pip install -e .

COPY *.env .

COPY configs configs

# using ENTRYPOINT means that options on the docker run command will be passed to the running command
ENTRYPOINT ["python", "./prodmon/plc_collect/main.py"]

