#! /usr/bin/python

import math

i = 1.0
while i < 30:
	print str(i) +" = "+str(math.log(math.pow(i,2))) +" "+str(math.pow(1+math.log(i),2))
	i+=1.0

