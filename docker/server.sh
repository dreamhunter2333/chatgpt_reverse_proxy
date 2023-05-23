#!/bin/bash

echo "Starting server"

if [ ! -z $user_data_dir ]
then
    rm -rf $user_data_dir/Singleton*
else
    rm -rf /tmp/.playwright/Singleton*
fi

python3 server.py
