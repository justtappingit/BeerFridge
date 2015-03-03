#! /bin/bash

for arg in "$@"
do
	echo $arg > /sys/class/gpio/export
	sleep 1
	echo "out" > /sys/class/gpio/gpio$arg/direction
	echo "Solid state relay pin #"$arg $v
	cat /sys/class/gpio/gpio$arg/value
done
