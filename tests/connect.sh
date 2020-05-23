#!/bin/bash

for ID in {1..200}
do
    message="{\"action\": \"test\", \"params\": [$2, \"$1-$ID\"]}";
    length=${#message}
    { echo "$length~$message"; } | telnet localhost 5000;
done
