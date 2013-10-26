#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: lcd_class.py,v 1.17 2013/07/02 13:16:54 bob Exp $
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
#
# Author : Bob Rathbone
# Site	 : http://www.bobrathbone.com
#
# From original LCD routines : Matt Hawkins
# Site	 : http://www.raspberrypi-spy.co.uk
#
# Expanded to use 4 x 20  display
#
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc'
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#

import os
import time
import RPi.GPIO as GPIO

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)	     - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0	     - NOT USED
# 8 : Data Bit 1	     - NOT USED
# 9 : Data Bit 2	     - NOT USED
# 10: Data Bit 3	     - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND

# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
#LCD_D4 = 21	# Rev 1 Board
LCD_D4 = 25	# Rev 2 Board
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
LED_ON = 15

# Define LCD device constants
LCD_LINES = 2
LCD_WIDTH = 16	  # Default characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

# Timing constants
E_PULSE = 0.00005
E_DELAY = 0.00005


class LCDBaseIO:
	
	def initializeIO( self ):
		# LED outputs
		GPIO.setwarnings(False)      # Disable this line on Rev 1 boards
		GPIO.setmode(GPIO.BCM)	     # Use BCM GPIO numbers
		GPIO.setup(LCD_E, GPIO.OUT)  # E
		GPIO.setup(LCD_RS, GPIO.OUT) # RS
		GPIO.setup(LCD_D4, GPIO.OUT) # DB4
		GPIO.setup(LCD_D5, GPIO.OUT) # DB5
		GPIO.setup(LCD_D6, GPIO.OUT) # DB6
		GPIO.setup(LCD_D7, GPIO.OUT) # DB7
		GPIO.setup(LED_ON, GPIO.OUT) # led backlight

		self._byte_out(0x33,LCD_CMD)
		self._byte_out(0x32,LCD_CMD)
		self._byte_out(0x28,LCD_CMD)
		self._byte_out(0x0C,LCD_CMD)
		self._byte_out(0x06,LCD_CMD)
		self._byte_out(0x01,LCD_CMD)
		time.sleep(0.3)
		return
	
	# Output byte to Led  mode = Command or Data
	def _byte_out( self, bits, mode ):
		# Send byte to data pins
		# bits = data
		# mode = True  for character
		#	 False for command
		GPIO.output(LCD_RS, mode) # RS

		# High bits
		GPIO.output(LCD_D4, False)
		GPIO.output(LCD_D5, False)
		GPIO.output(LCD_D6, False)
		GPIO.output(LCD_D7, False)
		if bits&0x10==0x10:
			GPIO.output(LCD_D4, True)
		if bits&0x20==0x20:
			GPIO.output(LCD_D5, True)
		if bits&0x40==0x40:
			GPIO.output(LCD_D6, True)
		if bits&0x80==0x80:
			GPIO.output(LCD_D7, True)

		# Toggle 'Enable' pin
		time.sleep(E_DELAY)
		GPIO.output(LCD_E, True)
		time.sleep(E_PULSE)
		GPIO.output(LCD_E, False)
		time.sleep(E_DELAY)

		# Low bits
		GPIO.output(LCD_D4, False)
		GPIO.output(LCD_D5, False)
		GPIO.output(LCD_D6, False)
		GPIO.output(LCD_D7, False)
		if bits&0x01==0x01:
			GPIO.output(LCD_D4, True)
		if bits&0x02==0x02:
			GPIO.output(LCD_D5, True)
		if bits&0x04==0x04:
			GPIO.output(LCD_D6, True)
		if bits&0x08==0x08:
			GPIO.output(LCD_D7, True)

		# Toggle 'Enable' pin
		time.sleep(E_DELAY)
		GPIO.output(LCD_E, True)
		time.sleep(E_PULSE)
		GPIO.output(LCD_E, False)
		time.sleep(E_DELAY)
		return

# End of Lcd class

class LCD( LCDBaseIO ):
	# LCD width
	width = LCD_WIDTH
	
	# If display can support umlauts set to True else False
	display_umlauts = True
	
	# enable raw mode (testing only)
	raw_mode = False
	
	# addresses of each lcd line (ignore last two for 2-line-lcds)
	line_addresses = [ LCD_LINE_1, LCD_LINE_2, LCD_LINE_3, LCD_LINE_4 ]
	
	# lines
	lines = [ '', '', '', '' ]
	
	# constructor
	def __init__( self ):
		super( LCD, self ).__init__()
		return
		
	# initialize function for delayed init
	def initialize( self ):
		self.initializeIO()
		
	# Set text at line
	def setLine( self, line_number, text ):
		self.lines[ line_number - 1 ] = text
		
	def getLine( self, line_number ):
		return self.lines[ line_number - 1 ]
		
	def getLineAddress( self, line_number ):
		return self.line_addresses[ line_number - 1 ]
		
	# Display text at line directly
	def displayLine( self, line, text ):
		self.setLine( line, text )
		self.display( line, text )
		
	# Display text at line directly
	def display( self, line, text ):
		if line > 0 and line <= LCD_LINES:
			#print("i: {}".format(line))
			self._byte_out( self.getLineAddress( line ), LCD_CMD )
			self._string( text )
		
	# Send string to display
	def _string( self, message ):
		s = message.ljust( self.width, " " )
		if not self.raw_mode:
			s = self.translateSpecialChars(s)
		for i in range( self.width ):
			self._byte_out( ord(s[i] ), LCD_CHR )
		#print( "Display: '{}'".format( message ) )
		return
		
	# Set the display width
	def setWidth(self,width):
		self.width = width
		return
	
	# Enable/disable backlight
	def setBacklightEnabled( self, enable_light ):
		GPIO.output( LED_ON, bool(enable_light) )
		return

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
		for line_index in range( LCD_LINES ):
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

