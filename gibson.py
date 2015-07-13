#! /usr/bin/python
import time
import sys,traceback
import logging
import math
import os

from command_server import myServer
from side import Side,RunStatus
#/sys/bus/w1/devices/28-0000066eb94b/value #air temp
#/sys/bus/w1/devices/28-00000670579a/value #beer temp

logging.basicConfig(filename="/home/pi/beer_fridge/logFile.log",level=logging.DEBUG)
logger = logging.getLogger(__name__)

targetTemp = 71 
graceDistance = .75		#Temp to turn off the elements inside of bands!!
tempRange = 1.5	#Bracket of acceptable air temp	

heatRelay = 27 #GPIO pin number
coldRelay = 17 #GPIO pin number

coldSide = Side("COLD",-1, coldRelay, logger)
hotSide = Side("HOT",1, heatRelay, logger)

runStatus = RunStatus()
coldSide.setTempBands(targetTemp, tempRange, graceDistance) #Set initial temperature rules, can change during cycle
hotSide.setTempBands(targetTemp, tempRange, graceDistance)

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

	#Determine if one side is going to fast adjust, calc act/decact on that base
	if side.useMyAdjustedTemp() and otherSide.useMyAdjustedTemp():
		log("WARNING!! BOTH SIDES WANT TO FAST ADJUST!!")
		adjustedTarget = side.getFastAdjustedTargetTemp()
	elif otherSide.useMyAdjustedTemp():
		adjustedTarget = otherSide.getFastAdjustedTargetTemp()
	else:
		adjustedTarget = side.getFastAdjustedTargetTemp()

	if side.active:
		if side.shouldDeactivate(adjustedTarget):
			side.deactivate()	
			log("Turning off "+side.name+" currentTemp "+str(side.currTemp)+" uptime: "+str(side.getCycleTime())+" Diff: "+str(side.getCycleTempDiff()))
			return True
		else:
			log("Continuing "+side.name+"  air temp "+str(side.currTemp)+" beer temp "+str(side.beerTemp)+" uptime "+str(side.getUpTime()))
			return True

	else:
		if side.shouldActivate(adjustedTarget):
			if side.getDownTime() < 300:
				log("WARNING "+side.name+" is attempting to flash (5 mins) "+str(side.currTime)+" "+str(side.cycle.stopTime))
				return True
			if otherSide.getDownTime() < 120:
				log("WARNING "+side.name+" is attempting to immediately activate after other side, 2 min cool down "+str(side.currTime))
				return True
			if otherSide.active:
				log("WARNING "+side.name+" activating with other side on, turning off other side")
				otherSide.deactivate()
			log("Activating "+side.name+" current temp: "+str(side.currTemp)+" Target:"+str(side.target))
			side.activate()
			return True

def getReport(coldSide, hotSide):
	report =""
	report += "CurrTemp: "+str(coldSide.currTemp)+" BeerTemp: "+str(coldSide.beerTemp)+"\n"
	report += "Cold: \n"+coldSide.getReport()+"\n"
	report += "Hot: \n"+hotSide.getReport()+"\n"
	report +="Stopped: "+str(runStatus.stop)+" "
	report += "LastAction Mins ago: "+str((coldSide.currTime-max(coldSide.getLastOff(), hotSide.getLastOff()))/60)
	return report

def handleCommands(comServ, coldSide, hotSide):
	try:
		while len(comServ.commands) > 0:
			command  = comServ.commands.popleft().strip()
			log("Processing command: "+command)
			comArray = command.strip().split(" ")
			if len(comArray) == 0:
				log("Bad command parse")
				continue
			com = str(comArray[0].strip()).lower()
			if com == "r" or com =="d":
				log("Report")
				r = ""
				r = getReport(coldSide, hotSide)
				log(r)
				comServ.sendMessage(r)
			elif com == "q":
				log("Disable")
				runStatus.run = False
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
			elif com == "eside":
				log("Set enable side")
				if len(comArray) < 2:
					comServ.sendMessage("Must include HOT or COLD")
				else:
					s = str(comArray[1]).upper()
					if s == "HOT":
						hotSide.enabled = True
						comServ.sendMessage("Hot side enabled")
					elif s == "COLD":
						coldSide.enabled = True
						comServ.sendMessage("Cold side enabled")
					else:
						comServ.sendMessage("Unknown side")
			elif com == "dside":
				log("Set disable side")
				if len(comArray) < 2:
					comServ.sendMessage("Must include HOT or COLD")
				else:
					s = str(comArray[1]).upper()
					if s == "HOT":
						hotSide.enabled = False
						comServ.sendMessage("Hot side disabled")
					elif s == "COLD":
						coldSide.enabled = False
						comServ.sendMessage("Cold side disabled")
					else:
						comServ.sendMessage("Unknown side")
			elif com == "stop":
				log("Stopping from command")
				coldSide.deactivate()
				hotSide.deactivate()
				runStatus.stop= True
				comServ.sendMessage("Stopping")
			elif com == "start":
				log("Starting from command")
				runStatus.stop = False
				comServ.sendMessage("Starting")
		
				
			elif com == "?":
				log("Command list")
				s=""
				s+="r (report status of heating cooling temp and settings)\n"
				s+="d (report status of heating cooling temp and settings)\n"
				s+="q (disable and shut down)\n"
				s+="set [temp] (change the target tempature to temp)\n"
				s+="w [width] (set the variance width in degreess to width)\n"
				s+="stop (stop heating and cooling, shut off relays)\n"
				s+="start (start heating cooling)\n"
				s+="eside [side] (enable side hot/cold)\n"
				s+="dside [side] (disable side hot/cold)\n"
				comServ.sendMessage(s)
				log(s)
			else:
				log("unknown command: "+com)

	except:
		log("Bad command! ")
		log(str(sys.exc_info()[0]))
		traceback.print_exc(file=sys.stdout)
		comServ.sendMessage("BAD COMMAND!")




commandServer = myServer(logging)

try:
 commandServer.start()
 while(runStatus.run):
	currAirTemp = getTemp(airProbe)
	currBeerTemp = getTemp(beerProbe)
	currTime = int(time.time())
	coldSide.setUpdateValues(currTime, currAirTemp, currBeerTemp)
	hotSide.setUpdateValues(currTime, currAirTemp, currBeerTemp)

	handleCommands(commandServer, coldSide, hotSide)
	if runStatus.stop:
		if coldSide.active:
			coolSide.deactivate()
		if hotSide.active:
			hotSide.deactivate()
		log("Stopped")
		time.sleep(2)
		continue
	if coldSide.active and hotSide.active:
		log("You royally messed up!")
		runStatus.run = False
		continue
	if not (coldSide.stateSync() and hotSide.stateSync()):
		log("State and side class out of sync shutting down" + str(coldSide.active)+" "+str(coldSide.relayState)+" "+str(hotSide.active)+" "+str(hotSide.relayState))
		runStatus.run = False
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
 log(str(sys.exc_info()[0]))
 print "Attempting to send warning email"
 os.popen("echo \"Beer fridge has shutdown! Check log for details.\" |mail -s \"Beer Fridge Exception!\" nope@gmail.com")
 

allOff() # Program end turn off everyhing
commandServer.shutdown()
