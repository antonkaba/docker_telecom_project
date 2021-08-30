#!/bin/bash

if ssh -o PasswordAuthentication=No root@$1 -p $2 true \
     |& grep -q "Connection refused"
then
    echo "Server is not reachable!"
else
    echo "Server reachable."
fi
