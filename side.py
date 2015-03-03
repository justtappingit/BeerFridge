#! /usr/bin/python

class Cycle:
	count = 0
	startTemp = 0
	startTime = 0
	totalTime = 0
	totalTemp = 0
	stopTime = 0
	lastDiff = 0	
	
	def __init__(self):
		pass

	def start(self, time , temp):
		self.startTime = time
		self.startTemp = temp
		self.count += 1

	def stop(self, time, tempDiff):
		if tempDiff < 0:
			print "CRAP TEMP DIFF < 0 what happened?"
		self.totalTime += time - self.startTime
		self.totalTemp += tempDiff
		self.stopTime = time
		self.lastDiff = tempDiff
	
	def avgCycleTempChange(self):
		if self.count == 0:
			return 0.0
		else:
			return float(self.totalTemp)/count
	def avgCycleTime(self):
		if self.count == 0:
			return 0.0
		else:
			return float(self.totalTime)/count
	def avgTempChangeRate(self):
		if self.count == 0:
			return 0.0
		else:
			return float(self.totalTemp)/self.totalTime
	def lastCycleTime(self):
		return self.stopTime - self.startTime



class Side:
	on = 1
	off = 0
	active = False 
	variance = 0
	target = 0
	cutOff = 0
	cycle = Cycle()
	currTime = 0
	currTemp = 0
	relayState = -1
	def __init__(self,name, side, relay):
		self.mySide = side
		self.name = name
		self.relay = relay

	def printSide(self):
		print str(self.mySide)

	def getLastOff():
		return self.cycle.stopTime

	def stateSync(self):
		return self.active == self.relayState
	def getCycleTime(self):
		return str(self.cycle.lastCycleTime())

	def getCycleTempDiff(self):
		return str(self.cycle.lastDiff)

	def getUpTime(self):
		return self.currTime - self.cycle.startTime

	def getDownTime(self):
		return self.currTime - self.cycle.stopTime
	
	def setUpdateValues(self, time, temp):
		self.currTime = time
		self.currTemp = temp
		self.relayState = self.getRelayState()

	def getTempChangeDiff(self, start, stop):
		return (stop-start) * self.mySide

	def setTempBands(self, targetTemp, varTemp, cut):
		self.target = targetTemp
		self.variance = varTemp
		self.cutOff = cut

	def shouldActivate(self):
		if self.target == 0:
			print "Activate not set!"
			return False
		#print str(self.mySide) + " "+str(self.target)+ " "+str(sampledTemp)+" "+str(self.variance)
		return self.mySide*(self.target - self.currTemp) > self.variance and not(self.active)

	def shouldDeactivate(self):
		return (-1*self.mySide)*(self.target-self.currTemp) >= (self.variance - self.cutOff) and (self.active)#using the inverse to persist var-cutoff form
		

	def activate(self):
		self.active = True
		self.cycle.start(self.currTime, self.currTemp)
		self.setRelay(self.on)

	def deactivate(self):
		self.active = False
		diff = self.getTempChangeDiff(self.cycle.startTemp, self.currTemp)
		self.cycle.stop(self.currTime, diff)
		self.setRelay(self.off)

	def setRelay(self, val):
        	file=open("/sys/class/gpio/gpio"+str(self.relay)+"/value", "w")
        	file.write(str(val))
        	file.close()

	def getRelayState(self):
        	file=open("/sys/class/gpio/gpio"+str(self.relay)+"/value", "r")
	        s = int(file.readline().strip())
        	file.close()
	        return s


