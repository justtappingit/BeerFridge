#! /usr/bin/python
import time
import sys,traceback
import logging

from side import Side
#/sys/bus/w1/devices/28-0000066eb94b/value #air temp
#/sys/bus/w1/devices/28-00000670579a/value #beer temp

logging.basicConfig(filename="/home/pi/beer_fridge/logFile.log",level=logging.DEBUG)
targetTemp = 80 
desiredTemp = targetTemp 	#Adjuted desired temp of the beer and base temp for air temp
graceDistance = .75		#Temp to turn off the elements inside of bands 
tempRange = 2			#Bracket of acceptable air temp	

heatRelay = 17 #GPIO pin number
coldRelay = 27 #GPIO pin number

coldSide = Side("COLD",-1, coldRelay)
hotSide = Side("HOT",1, heatRelay)

coldSide.setTempBands(targetTemp, tempRange, graceDistance) #Set initial temperature rules, can change during cycle
hotSide.setTempBands(targetTemp, tempRange, graceDistance)


run = True
airProbe = "28-0000066eb94b" #Serial number for temp sensor
beerProbe = "28-00000670579a" #Serial number for temp sensor


def getTemp(name):
	file=open("/sys/bus/w1/devices/"+airProbe+"/w1_slave","r")
	file.readline().strip()
	line = file.readline().strip().split()
	temp = (float(line[len(line)-1].split("=")[1])/1000)*(9.0/5.0)+32
	file.close()
	return temp

def log(line):
	logline = time.ctime()+" "+line
	print logline
	logging.info(logline)

def allOff():
	coldSide.setRelay(0)
	hotSide.setRelay(0)

def runSide(side, otherSide):
	if side.active:
		if side.shouldDeactivate():
			side.deactivate()	
			log("Turning off "+side.name+" currentTemp "+str(side.currTemp)+" uptime: "+str(side.getCycleTime())+" Diff: "+str(side.getCycleTempDiff()))
			return True
		else:
			log("Continuing "+side.name+"  temnp "+str(side.currTemp)+" uptime "+str(side.getUpTime()))
			return True

	else:
		if side.shouldActivate():
			if side.getDownTime() < 10:
				log("WARNING "+side.name+" is attempting to flash")
				return True
			if otherSide.active:
				log("WARNING "+side.name+" activating with other side on, turning off other side")
				otherSide.deactivate()
			log("Activating "+side.name+" current temp: "+str(side.currTemp))
			side.activate()
			return True


try:
 while(run):
	currAirTemp = getTemp(airProbe)
	currBeerTemp = getTemp(beerProbe)
	currTime = int(time.time())
	coldSide.setUpdateValues(currTime, currAirTemp)
	hotSide.setUpdateValues(currTime, currAirTemp)

	if coldSide.active and hotSide.active:
		log("You royally messed up!")
		run = False
		continue
	if not (coldSide.stateSync() and hotSide.stateSync()):
		log("State and side class out of sync shutting down" + str(coldSide.active)+" "+str(coldSide.relayState)+" "+str(hotSide.active)+" "+str(hotSide.relayState))
		run = False
		continue


	if runSide(hotSide, coldSide) or runSide(coldSide, hotSide):
		time.sleep(2)
		continue

	log("Nothing to do. Mins since last stop action: " + str(currTime-max(coldSide.getLastOff(), hotSide.getLastOff())/60)+" Temp: "+str(currAirTemp)+" Heat: "+str(heatState)+" Cold: "+str(coldState))
	time.sleep(2)

except: #Catch everything we can so we gracefully shutdown 
 print "Unexpected error: "+str(sys.exc_info()[0])
 traceback.print_exc(file=sys.stdout)
 allOff()

allOff() # Program end turn off everyhing
