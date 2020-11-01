#! /bin/bash

docker network create replicated-log-network

echo build-n-run Master
bash build-n-run-master.bash

echo build-n-run Secondaries
bash build-n-run-secondaries.bash