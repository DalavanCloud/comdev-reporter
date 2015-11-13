# Script to run "svn add" and redirect standard output to /var/log/www-data
# adds header and trailer to any output

# Output log file is named after the SVN directory name plus the suffix _YYYY-MM
# This ensures that at most one month's data is in each log file

# Sample crontab entry:
# 40 * * * *      cd /var/www/reporter.apache.org/scripts && ./svnadd.sh ../data/releases

STARTED=$(date '+%Y-%m-%d %H:%M:%S')

SVNDIR=${1?SVN directory}

LOGDIR=/var/log/www-data

BASE=$(basename $SVNDIR)

YYMM=$(date '+%Y-%m')

exec  >>${LOGDIR}/${BASE}_${YYMM}.log

svn status $SVNDIR | awk '/^\? / {print $2}' | xargs -r svn add | \
{
    # Read one line first
    IFS= read -r line && \
    {
        # add header
        echo
        echo '>>>'
        echo "Starting  'svn add $SVNDIR' at $STARTED"
        echo "$line"

        # read the rest of the lines
        while IFS= read -r line
        do
            echo "$line"
        done
        
        # add trailer
        echo "Completed 'svn add $SVNDIR' at $(date '+%Y-%m-%d %H:%M:%S')"
        echo '<<<'
    }
}
