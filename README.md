# Replicated log

Replicated log is a distributed master-secondary system.
Consists of two subprojects - master and secondary nodes. Each has an HTTP API for external clients and gRPC for internal communication. 
Master receives a message and replicates it to secondary nodes.

Implemented on Python.

## Prerequisites

To run the project in Docker, a single dependency is installed Docker.

To run the project without Docker
- Python 3.8
- Other dependencies are listed in requirements.txt files, located at the root of each subproject.


## Run in Docker

The project uses docker-compose to build-n-deploy. To run in Docker execute the following terminal commands:

```bash
docker-compose build
docker-compose up
```

## Run without Docker
Subprojects master and secondary are located in separate folders master/ and secondary/ respectively.
Before running a subproject, install required packages:
```bash
pip install -r requirements.txt
```
The entry point for each subproject is a main.py file.

## External API
### Master node
#### POST /api 
Appends a message to master's memory and replicates it to secondary nodes via gRPC.

Request body model should contain JSON with "message" property. Example:

```json
 {"message": "some message"}
```
Returns request HTTP status.

#### GET /api
Returns master's in-memory saved messages list.
Response example:

```json
["first message", "second message"]
```

#### GET /api/health
Returns secondaries health.
Response example:

```json
{"secondary-address1": "Healthy", "secondary-address2": "Unhealthy"}
```

### Secondary node
#### GET /api
Returns secondary's in-memory replicated messages list.
Response example:

```json
["first message", "second message"]
```
