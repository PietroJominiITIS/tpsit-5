#!/bin/sh

#
# Pietro Jomini
# 13.04.2021
#
# Runs two clients in parallel.
# Redirects the output to out-client{n}.txt

python client.py >out-client1.txt &
python client.py >out-client2.txt &

wait
