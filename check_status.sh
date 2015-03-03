#! /bin/bash


if [ $# -eq 0 ]; then
	echo "Searching for loaded pins"
	for i in $(ls /sys/class/gpio/ | egrep -v gpiochip0 | grep gpio | cut -d"o" -f2);do
		echo "Pin: "$i
		cat /sys/class/gpio/gpio$i/value

	done
	exit

fi


for arg in "$@"
do
	echo "Pin: "$arg
	cat /sys/class/gpio/gpio$arg/value
done
