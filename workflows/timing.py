#!/usr/bin/env python3

import time
import math

class Timer:
	def __init__(self):
		self.__start = time.time()
		self.__laps = []

	def _getDuration(self, duration):
		(m, s) = divmod(math.floor(duration), 60)
		(h, m) = divmod(m, 60)
		return "{0:d} hours {1:02d} minutes {2:02d} seconds".format(h, m, s)

	def start(self):
		self.__start = time.time()

	def lap(self):
		""" Return a string representation of the LAP duration """
		self.__laps.append(time.time())
		previous = self.__start
		if len(self.__laps) > 1:
			previous = self.__laps[-2]
		return self._getDuration(self.__laps[-1] - previous)

	def stop(self):
		""" Return a string representation of the whole period the clock has been active.
			It will reset the start and LAPS information
		"""
		duration = self._getDuration(time.time() - self.__start)
		self.__start = time.time()
		self.__laps = []
		return duration

if __name__ == "__main__":
	# Unit test
	timer = Timer()
	time.sleep(2)
	print(timer.lap())
	time.sleep(3)
	print(timer.lap())
	time.sleep(6)
	print(timer.stop())