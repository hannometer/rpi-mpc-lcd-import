#!/usr/bin/env python



import os
import sys
import time
import string
import datetime

from mpd import MPDClient

# Class imports
from daemon3_class import Daemon
#from lcd_class    import ScrollingLCD
from lcd_i2c_class import ScrollingLCD

lcd = ScrollingLCD()
mpc = MPDClient()

# LCD-MPC Daemon
class LCDMPCDaemon( Daemon ):

	def __del__( self ):
		print("Stopping daemon")
		lcd.stopScrollThread()
		lcd.displayLine( 1, 'LCD-Daemon off')
		lcd.displayLine( 2, '')
		lcd.disableBacklight()
		time.sleep(3)
		lcd.clear()

	def connectMPD( self ):
		connected = False
		try_again_time = 1
		try_again_time_max = 6
		while not connected:
			try:
				mpc.connect( "localhost", 6600 )
				connected = True
				print("Successfully connected to mpd")
			except:
				print("Couldn't connect to mpd, trying again in {}s".format(try_again_time))
				time.sleep( try_again_time )
				try_again_time = min( try_again_time * 1.5, try_again_time_max )

	def run(self):
		# Initialize lcd and mpc
		lcd.initialize()
		lcd.disableBacklight()
		lcd.setScrollSpeed( 5 )
		lcd.displayLine( 1, 'LCD-Daemon on')
		lcd.displayLine( 2, '')
		
		self.connectMPD()
		lcd.startScrollThread()

		# Main processing loop
		while True:
			songinfo = self.getCurrentSongInfo()
			print("[isPlaying: {}] {}: {}".format(self.isPlaying(), songinfo['artist'], songinfo['title']))
			lcd.setBacklightEnabled( self.isPlaying() )
			lcd.setLine( 1, songinfo['artist'] )
			#lcd.setLine( 1, 'Buena Vista Social Club' )
			lcd.setLine( 2, songinfo['title'] )
			time.sleep( 1 )

	def isPlaying(self):
		return mpc.status()['state'] == 'play'

	def getCurrentSongInfo(self):
		info = mpc.currentsong()
		ret_info = dict(artist='Unknown', title='Unknown')

		if not ( 'artist' in info or 'title' in info ):
			return ret_info

		if 'artist' in info:
			ret_info['artist'] = info['artist']
			ret_info['title'] = info['title']
		else:
			title_sections = info['title'].split(' - ')
			if len(title_sections) > 1:
				ret_info['artist'] = title_sections[0]
				ret_info['title'] = title_sections[1]

		return ret_info


def no_interrupt():
	return false
