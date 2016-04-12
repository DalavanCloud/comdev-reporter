# Simple SMTP interface
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

def sendMail(subject, body, recipients, sender='no-reply@reporter.apache.org', port=25):
    # Create a text/plain message
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipients
    smtp = smtplib.SMTP('localhost', port)
    smtp.sendmail(sender, [recipients], msg.as_string())
    smtp.quit()

if __name__ == '__main__':
    # for testing locally:
    # sudo postfix start # MacoxX
    # or start a debug server => need to change the SMTP port above
    # python -m smtpd -n -c DebuggingServer localhost:1025
    sendMail('Example SMTP message', "The quick brown fox ...", 'no-one')
    print("Sent")