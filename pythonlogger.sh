# Script to redirect standard output of a python script to /var/log/www-data

# Output log file is named after the script file name plus the suffix _YYYY-MM
# This ensures that at most one month's data is in each log file

# Sample usage:
# cd .../scripts/cronjobs && ./pythonlogger.sh parsepmcs.py

SCRIPT=${1?Script name}

LOGDIR=/var/log/www-data

BASE=$(basename $SCRIPT .py)

YYMM=$(date '+%Y-%m')

exec  >>${LOGDIR}/${BASE}_${YYMM}.log
echo
echo '>>>'
echo Starting $SCRIPT at $(date)
export

python -u $SCRIPT 

echo Completed $SCRIPT at $(date)
echo '<<<'
