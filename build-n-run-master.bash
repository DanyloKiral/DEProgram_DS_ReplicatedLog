#! /bin/bash
imageName=ds_replicatedlog_masternode_image
containerName=master_node

docker build -t $imageName -f master/Dockerfile  .

echo Delete old container...
docker rm -f $containerName

echo Run new container...
docker run -d -p 5000:5000 --name $containerName --network replicated-log-network --network-alias master-node $imageName