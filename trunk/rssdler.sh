#!/bin/sh
# INSTRUCTIONS (assumes debian-based distro)
# save to /etc/init.d/rssdler (NOT rssdler.sh!!)
# change USER, NAME, DAEMON, CONFIGFILE to suit preferences
# in your RSSDler config file, make sure you specify: daemonInfo, workingDir
# chmod 755 /etc/init.d/rssdler
# sudo chown root:root /etc/init.d/rssdler
# sudo update-rc.d rssdler defaults

########
#BEGIN CONFIG
########
# user to run RSSDler as
USER='user'
# name you saved RSSDler to
NAME='rssdler.py'
#directory you put rssdler, plus $NAME is the name of it (you set it above though)
DAEMON="/home/$USER/.rssdler/$NAME"
#where is the config file found
CONFIGFILE="/home/$USER/.rssdler/config.txt"
########
#END CONFIG
########

WORKINGDIR=`cat "$CONFIGFILE" | grep -i "^workingDir" | sed -r "s/^workingDir\s*=\s*(.*)/\1/i"`
DAEMON_ARGS="-d -c "$CONFIGFILE""
PIDFILE=`cat "$CONFIGFILE" | grep -i "^daemonInfo" | sed -r "s/^daemonInfo\s*=\s*(.*)/\1/i"`
PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="RSSDler"
SCRIPTNAME=/etc/init.d/rssdler

# Exit if the package is not installed
[ -x "$DAEMON" ] || exit 0

if [ -z $PIDFILE ] ; then
	echo "you didn't specify daemonInfo in your config file"
	exit 1
fi

if [ -z $WORKINGDIR ] ; then
	echo "you didn't specify a workingDir in your config file"
	exit 1
fi

if ! [ -d "$WORKINGDIR" ] ; then
	echo "the workingDir you specified does not exist"
	exit 1
fi

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
. /lib/lsb/init-functions

do_start()  {
	if ps -p `cat "$PIDFILE"` -o comm= > /dev/null 2>&1 ; then
		# daemon alread running
		return 1
	fi
	start-stop-daemon --start --quiet --pidfile $PIDFILE -c $USER --exec $DAEMON -- \
		$DAEMON_ARGS \
		|| return 2
}

do_stop()
{
	"$DAEMON" -k -c "$CONFIGFILE" || return 2
}

cd "$WORKINGDIR"

case "$1" in
  start)
	[ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC" "$NAME"
	do_start
	case "$?" in
		0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
		2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	esac
	;;
  stop)
	[ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
	do_stop
	case "$?" in
		0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
		2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	esac
	;;
  restart|force-reload)
	#
	# If the "reload" option is implemented then remove the
	# 'force-reload' alias
	#
	log_daemon_msg "Restarting $DESC" "$NAME"
	do_stop
	case "$?" in
	  0|1)
		do_start
		case "$?" in
			0) log_end_msg 0 ;;
			1) log_end_msg 1 ;; # Old process is still running
			*) log_end_msg 1 ;; # Failed to start
		esac
		;;
	  *)
	  	# Failed to stop
		log_end_msg 1
		;;
	esac
	;;
  *)
	echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload}" >&2
	exit 3
	;;
esac

:
