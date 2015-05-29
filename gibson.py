#! /usr/bin/python
import time
import sys,traceback
import logging
import math

from command_server import myServer
from side import Side
#/sys/bus/w1/devices/28-0000066eb94b/value #air temp
#/sys/bus/w1/devices/28-00000670579a/value #beer temp

logging.basicConfig(filename="/home/pi/beer_fridge/logFile.log",level=logging.DEBUG)
logger = logging.getLogger(__name__)

targetTemp = 66 
graceDistance = .75		#Temp to turn off the elements inside of bands 
tempRange = 1		#Bracket of acceptable air temp	

heatRelay = 27 #GPIO pin number
coldRelay = 17 #GPIO pin number

coldSide = Side("COLD",-1, coldRelay, logger)
hotSide = Side("HOT",1, heatRelay, logger)

coldSide.setTempBands(targetTemp, tempRange, graceDistance) #Set initial temperature rules, can change during cycle
hotSide.setTempBands(targetTemp, tempRange, graceDistance)

run = True
stop = False

airProbe = "28-0000066eb94b" #Serial number for temp sensor
beerProbe = "28-00000670579a" #Serial number for temp sensor


def getTemp(name):
	file=open("/sys/bus/w1/devices/"+name+"/w1_slave","r")
	file.readline().strip()
	line = file.readline().strip().split()
	temp = (float(line[len(line)-1].split("=")[1])/1000)*(9.0/5.0)+32
	file.close()
	return temp

def log(line):
	logline = time.ctime()+" "+line
	print logline
	#logging.info(logline)
	logger.info(logline)

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
			log("Continuing "+side.name+"  air temp "+str(side.currTemp)+" beer temp "+str(side.beerTemp)+" uptime "+str(side.getUpTime()))
			return True

	else:
		if side.shouldActivate():
			if side.getDownTime() < 10:
				log("WARNING "+side.name+" is attempting to flash "+str(side.currTime)+" "+str(side.cycle.stopTime))
				return True
			if otherSide.active:
				log("WARNING "+side.name+" activating with other side on, turning off other side")
				otherSide.deactivate()
			log("Activating "+side.name+" current temp: "+str(side.currTemp)+" Target:"+str(side.target))
			side.activate()
			return True

def getReport(coldSide, hotSide):
	report =""
	report += "CurrTemp: "+str(coldSide.currTemp)+"\n"
	report += "Cold: \n"+coldSide.getReport()+"\n"
	report += "Hot: \n"+hotSide.getReport()+"\n"
	report +="Stopped: "+str(stop)+" "
	report += "LastAction Mins ago: "+str((coldSide.currTime-max(coldSide.getLastOff(), hotSide.getLastOff()))/60)
	return report

def handleCommands(comServ, coldSide, hotSide):
	global run, stop
	try:
		while len(comServ.commands) > 0:
			command  = comServ.commands.popleft().strip()
			log("Processing command: "+command)
			comArray = command.strip().split(" ")
			if len(comArray) == 0:
				log("Bad command parse")
				continue
			com = str(comArray[0].strip())
			if com == "r" or com =="d":
				log("Report")
				r = ""
				r = getReport(coldSide, hotSide)
				log(r)
				comServ.sendMessage(r)
			elif com == "D":
				log("Disable")
				run = False
			elif com == "set":
				log("Set temp")
				if len(comArray) < 2:
					comServ.sendMessage("Must incldue temp")
				else:
					t = float(comArray[1])
					targetTemp = t 
					coldSide.target = targetTemp
					hotSide.target = targetTemp
					comServ.sendMessage("Temp set to "+str(t))
					log("Temp set "+str(t))
				
			elif com == "w":
				log("Set width")
                                if len(comArray) < 2:
                                        comServ.sendMessage("Must incldue variance")
                                else:
                                        t = float(comArray[1])
					tempRange = t
                                        coldSide.variance = tempRange
                                        hotSide.variance = tempRange
                                        log("Variance set "+str(t))
					comServ.sendMessage("Width set to "+str(t))
			elif com == "stop":
				log("Stopping from command")
				stop= True
				comServ.sendMessage("Stopping")
			elif com == "start":
				log("Starting from command")
				stop = False
				comServ.sendMessage("Starting")
				
			elif com == "?":
				log("Command list")
				s=""
				s+="r (report status of heating cooling temp and settings)\n"
				s+="d (report status of heating cooling temp and settings)\n"
				s+="D (disable and shut down)\n"
				s+="set [temp] (change the target tempature to temp)\n"
				s+="w [width] (set the variance width in degreess to width)\n"
				s+="stop (stop heating and cooling, shut off relays)\n"
				s+="start (start heating cooling)\n"
				comServ.sendMessage(s)
			else:
				log("unknown command: "+com)

	except:
		log("Bad command! ")
		log(str(sys.exc_info()[0]))
		traceback.print_exc(file=sys.stdout)




commandServer = myServer(logging)

try:
 commandServer.start()
 while(run):
	currAirTemp = getTemp(airProbe)
	currBeerTemp = getTemp(beerProbe)
	currTime = int(time.time())
	coldSide.setUpdateValues(currTime, currAirTemp, currBeerTemp)
	hotSide.setUpdateValues(currTime, currAirTemp, currBeerTemp)

	handleCommands(commandServer, coldSide, hotSide)
	if stop:
		if coldSide.active:
			coolSide.deactivate()
		if hotSide.active:
			hotSide.deactivate()
		log("Stopped")
		time.sleep(2)
		continue
	if coldSide.active and hotSide.active:
		log("You royally messed up!")
		run = False
		continue
	if not (coldSide.stateSync() and hotSide.stateSync()):
		log("State and side class out of sync shutting down" + str(coldSide.active)+" "+str(coldSide.relayState)+" "+str(hotSide.active)+" "+str(hotSide.relayState))
		run = False
		continue


	if runSide(hotSide, coldSide):
		time.sleep(2)
		continue
	if runSide(coldSide, hotSide):
		time.sleep(2)
		continue

	log("Nothing to do. Mins since last stop action: " + str((currTime-max(coldSide.getLastOff(), hotSide.getLastOff()))/60)+" Temp: "+str(currAirTemp)+" Heat: "+str(hotSide.relayState)+" Cold: "+str(coldSide.relayState))
	time.sleep(2)

except: #Catch everything we can so we gracefully shutdown 
 print "Unexpected error: "+str(sys.exc_info()[0])
 traceback.print_exc(file=sys.stdout)
 allOff()
 commandServer.shutdown()
 

allOff() # Program end turn off everyhing
commandServer.shutdown()
