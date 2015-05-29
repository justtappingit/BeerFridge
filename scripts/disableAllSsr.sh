#! /bin/bash


if [ $# -eq 0 ]; then
	echo "Searching for loaded pins"
	for i in $(ls /sys/class/gpio/ | egrep -v gpiochip0 | grep gpio | cut -d"o" -f2);do
		echo "Pin: "$i
		echo 0 > /sys/class/gpio/gpio$i/value
		cat /sys/class/gpio/gpio$i/value

	done
	exit

fi


for arg in "$@"
do
	echo "Pin: "$arg
	echo 0 > /sys/class/gpio/gpio$arg/value
	cat /sys/class/gpio/gpio$arg/value
done
