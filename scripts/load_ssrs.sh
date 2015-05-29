#! /bin/bash
#17 and 27 are what we have been using

if [ $# -eq 0 ]; then
	ssrs=( "17" "27" )
	echo "Auto loading 17 and 27"
	for i in "${ssrs[@]}";do
		echo $i > /sys/class/gpio/export
		sleep 1
		echo "out" > /sys/class/gpio/gpio$i/direction
		echo "Solid state relay pin #"$i $v
		cat /sys/class/gpio/gpio$i/value
	done
	exit
fi

for arg in "$@"
do
	echo $arg > /sys/class/gpio/export
	sleep 1
	echo "out" > /sys/class/gpio/gpio$arg/direction
	echo "Solid state relay pin #"$arg $v
	cat /sys/class/gpio/gpio$arg/value
done
