#!/usr/bin/env python

import os
import time
import smbus

from i2c_lcd_driver import lcd

class LCD:
	# LCD width
	width = 16
	
	# If display can support umlauts set to True else False
	display_umlauts = True
	
	# enable raw mode (testing only)
	raw_mode = False
	
	# lines
	lines = [ '', '', '', '' ]
	
	lcd_driver = lcd()

	# constructor
	def __init__( self ):
		#lcd_init()
		return
	
	def __del__( self ):
		self.lcd_driver.display_off()	
	
	# initialize function for delayed init
	def initialize( self ):
		self.lcd_driver.display_on()
		
	def clear( self ):
		self.lcd_driver.clear()

	# Set text at line
	def setLine( self, line_number, text ):
		self.lines[ line_number - 1 ] = text
		
	def getLine( self, line_number ):
		return self.lines[ line_number - 1 ]

	# Display text at line directly
	def displayLine( self, line, text ):
		self.setLine( line, text )
		self.display( line, text )
		
	# Display text at line directly
	def display( self, line, text ):
		if line <= 0 or line > len(self.lines):
			return

		if not self.raw_mode:
			text = self.translateSpecialChars(text)

		self.lcd_driver.display_string( text.ljust(self.width," "), line )
		#print( "Display: '{}'".format( text ) )
		
	# Set the display width
	def setWidth(self,width):
		self.width = width
		return
	
	# Enable/disable backlight
	def setBacklightEnabled( self, enable_light ):
		if enable_light == True:
			self.lcd_driver.backlight_on()
		else:
			self.lcd_driver.backlight_off()

	# Enable backlight
	def enableBacklight( self ):
		self.setBacklightEnabled( True )
		return
	
	# Disable backlight
	def disableBacklight( self ):
		self.setBacklightEnabled( False )
		return
	
	# Set raw mode on (No translation)
	def setRawMode( self, value ):
		self.raw_mode = value
		return

	# Display umlats if tro elese oe ae etc
	def displayUmlauts(self,value):
		self.display_umlauts = value
		return

	# Translate special characters (umlautes etc) to LCD values
	# See standard character patterns for LCD display
	def translateSpecialChars(self,sp):
		s = sp

		# Currency
		s = s.replace(chr(156), '#')	   # Pound by hash
		s = s.replace(chr(169), '(c)')	   # Copyright

		# Spanish french
		s = s.replace(chr(241), 'n')	   # Small tilde n
		s = s.replace(chr(191), '?')	   # Small u acute to u
		s = s.replace(chr(224), 'a')	   # Small reverse a acute to a
		s = s.replace(chr(225), 'a')	   # Small a acute to a
		s = s.replace(chr(232), 'e')	   # Small e grave to e
		s = s.replace(chr(233), 'e')	   # Small e acute to e
		s = s.replace(chr(237), 'i')	   # Small i acute to i
		s = s.replace(chr(238), 'i')	   # Small i circumflex to i
		s = s.replace(chr(243), 'o')	   # Small o acute to o
		s = s.replace(chr(244), 'o')	   # Small o circumflex to o
		s = s.replace(chr(250), 'u')	   # Small u acute to u
		s = s.replace(chr(193), 'A')	   # Capital A acute to A
		s = s.replace(chr(201), 'E')	   # Capital E acute to E
		s = s.replace(chr(205), 'I')	   # Capital I acute to I
		s = s.replace(chr(209), 'N')	   # Capital N acute to N
		s = s.replace(chr(211), 'O')	   # Capital O acute to O
		s = s.replace(chr(218), 'U')	   # Capital U acute to U
		s = s.replace(chr(220), 'U')	   # Capital U umlaut to U
		s = s.replace(chr(231), 'c')	   # Small c Cedilla
		s = s.replace(chr(199), 'C')	   # Capital C Cedilla

		# German
		s = s.replace(chr(196), "Ae")		# A umlaut
		s = s.replace(chr(214), "Oe")		# O umlaut
		s = s.replace(chr(220), "Ue")		# U umlaut

		if self.display_umlauts:
			s = s.replace(chr(223), chr(226))	# Sharp s
			s = s.replace(chr(246), chr(239))	# o umlaut
			s = s.replace(chr(228), chr(225))	# a umlaut
			s = s.replace(chr(252), chr(245))	# u umlaut
		else:
			s = s.replace(chr(228), "ae")		# a umlaut
			s = s.replace(chr(223), "ss")		# Sharp s
			s = s.replace(chr(246), "oe")		# o umlaut
			s = s.replace(chr(252), "ue")		# u umlaut
		return s


import threading

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class ScrollerUpdater( StoppableThread ):
	# ctor
	def __init__( self, lcd ):
		super(ScrollerUpdater, self).__init__()
		self.lcd = lcd
		#self.scroll_thread.target = self.run
		self.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
		
	# run
	def run( self ):
		while not self.stopped():
			# print("Update scroll.")
			self.lcd.updateScroll()
			time.sleep( 1 / self.lcd.scroll_speed )


class ScrollingLCD( LCD ):	
	# scroll speed
	scroll_speed = 5
	
	# phases of scrolling: pause - scroll right - pause - scroll left
	scroll_phase = [0, 0, 0, 0]

	# progress of scrolling in each phase
	scroll_progress = [0, 0, 0, 0]
	
	# pause between scrolling left/right [in cycles]
	scroll_pause = 5
	
	def __init__( self ):
		super( ScrollingLCD, self ).__init__()
		self.scroller_updater = ScrollerUpdater( self )
		
	def startScrollThread( self ):
		if not self.scroller_updater.isAlive():
			self.scroller_updater.start()
			
	def stopScrollThread( self ):
		self.scroller_updater.stop()
		
	# Set Scroll line speed (frequency of update) - Best values are 3-5 
	# Limited to between 20 and 1
	def setScrollSpeed( self, speed ):
		speed = min( speed, 20 )
		speed = max( speed, 1 )
		self.scroll_speed = speed
		return
			
	# Called from ScrollerUpdater
	def updateScroll( self ):
		for line_index in range( len(self.lines) ):
			line = self.lines[ line_index ]
			
			# don't do anything if nothing is to be shown or
			# if the strings are short enough
			if len( line ) <= self.width:
				self.display( line_index + 1, line )
				continue
			
			# diff to line width
			len_diff = len( line ) - self.width
			
			# Start pause - wait 5 cycles
			if self.scroll_phase[ line_index ] == 0:
				if self.scroll_progress[ line_index ] < self.scroll_pause:
					self.scroll_progress[ line_index ] += 1
					self.display( line_index + 1, line[ 0:self.width ] )
				else:
					self.scroll_phase[ line_index ] = 1
					self.scroll_progress[ line_index ] = 0
								
			# Scroll right - progress means: start offset of line
			elif self.scroll_phase[ line_index ] == 1:
				if self.scroll_progress[ line_index ] < len_diff:
					self.scroll_progress[ line_index ] += 1
					offset = self.scroll_progress[ line_index ];
					self.display( line_index + 1, line[ offset:offset+self.width ] )
				else:
					self.scroll_phase[ line_index ] = 2
					self.scroll_progress[ line_index ] = 0
								
			# End pause
			elif self.scroll_phase[ line_index ] == 2:
				if self.scroll_progress[ line_index ] < self.scroll_pause:
					self.scroll_progress[ line_index ] += 1
					self.display( line_index + 1, line[ len_diff:len_diff+self.width ] )
				else:
					self.scroll_phase[ line_index ] = 3
					self.scroll_progress[ line_index ] = 0
				
			# Scroll left
			elif self.scroll_phase[ line_index ] == 3:
				if self.scroll_progress[ line_index ] < len_diff:
					self.scroll_progress[ line_index ] += 1
					offset = len( line ) - self.width - self.scroll_progress[ line_index ];
					self.display( line_index + 1, line[ offset:offset+self.width ] )
				else:
					self.scroll_phase[ line_index ] = 0
					self.scroll_progress[ line_index ] = 0
				
			# shouldn't happen: reset phase to 0
			else:
				self.scroll_phase[ line_index ] = 0
				self.scroll_progress[ line_index ] = 0

def no_interrupt():
	return False

