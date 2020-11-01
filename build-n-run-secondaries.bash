#! /bin/bash
imageName=ds_replicatedlog_secondarynode_image

S1containerName=secondary_node1
S1port=5010

S2containerName=secondary_node2
S2port=5011

docker build -t $imageName -f secondary/Dockerfile  .

echo Delete old containers...
docker rm -f $S1containerName
docker rm -f $S2containerName

echo Run new container 1...
docker run -d -p $S1port:5000 --name $S1containerName --network replicated-log-network --network-alias secondary-node1 $imageName

echo Run new container 2...
docker run -d -p $S2port:5000 --name $S2containerName --network replicated-log-network --network-alias secondary-node2 $imageName