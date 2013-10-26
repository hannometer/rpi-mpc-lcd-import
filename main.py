#!/usr/bin/env python

from mpc_lcd_daemon import LCDMPCDaemon

daemon = LCDMPCDaemon('/tmp/lcd_mpc_daemon.pid')
#daemon.start()
daemon.run()
