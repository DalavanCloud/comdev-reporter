# Restart scandist as a nohup process
# TODO: this should really be integrated into system startup

pkill -u root -f "scandist.py foreground"
mv --backup=numbered nohup.out nohup.out.$(date -Idate)
nohup python -u scandist.py foreground &