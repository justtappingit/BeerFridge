#! /bin/bash

sudo modprobe w1-gpio

sudo modprobe w1-therm
sleep 1
echo "Probes loaded: "
ls /sys/bus/w1/devices | grep 28
