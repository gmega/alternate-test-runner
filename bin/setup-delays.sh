#!/usr/bin/env bash

tc qdisc del dev lo root
tc qdisc add dev lo root handle 1:0 prio bands 2 priomap 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
tc qdisc add dev lo parent 1:2 netem delay 500ms
tc filter add dev lo protocol ip parent 1:0 prio 1 u32 match ip dport 8081 0xffff flowid 1:2