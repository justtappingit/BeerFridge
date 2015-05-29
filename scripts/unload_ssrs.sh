#! /bin/bash


if [ $# -eq 0 ]; then
	for i in $(ls /sys/class/gpio/ | egrep -v gpiochip0 | grep gpio | cut -d"o" -f2);do
		echo $i > /sys/class/gpio/unexport
		echo "Solid state relay pin #"$i" unloaded"
	done
	exit

fi


for arg in "$@"
do
	echo $arg > /sys/class/gpio/unexport
	echo "Solid state relay pin #"$arg" unloaded"
done
