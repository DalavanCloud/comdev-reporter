# Simple SMTP interface
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

__SENDER__ = 'Reporter <apsite@apache.org>'
__RECIPIENTS__ = 'Site Development <site-dev@apache.org>'
__REPLY_TO__ = 'site-dev@apache.org'

def sendMail(subject, body='', recipients=__RECIPIENTS__, sender=__SENDER__, port=25, replyTo=__REPLY_TO__):
    # Create a text/plain message
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipients
    if replyTo != None:
        msg['Reply-To'] = replyTo
    smtp = smtplib.SMTP('localhost', port)
    smtp.sendmail(sender, [recipients], msg.as_string())
    smtp.quit()

if __name__ == '__main__':
    # for testing locally:
    # sudo postfix start # MacoxX
    # or start a debug server => need to change the SMTP port
    # python -m smtpd -n -c DebuggingServer localhost:1025
    sendMail('Test message, please ignore', "Thanks!")
    print("Sent")