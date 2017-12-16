SCRIPT=scandist.py

LOGDIR=/var/log/www-data

BASE=$(basename $SCRIPT .py)

YYMM=$(date '+%Y-%m')

exec  >>${LOGDIR}/${BASE}_${YYMM}_startup.log
echo
echo '>>>'
echo Starting $SCRIPT at $(date)
export

if [ "$1" = 'restart' ]
then
    python3 -u $SCRIPT stop
fi

LOGFILE=$LOGDIR/${BASE}_${YYMM}_daemon.log python3 -u $SCRIPT start

echo Completed $SCRIPT at $(date)
echo '<<<'
