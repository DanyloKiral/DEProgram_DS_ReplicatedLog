#! /bin/bash
imageName=ds_replicatedlog_masternode_image
containerName=master_node

cd master
docker build -t $imageName -f Dockerfile  .
echo Delete old container...
docker rm -f $containerName
echo Run new container...
docker run -d -p 5000:5000 --name $containerName $imageName