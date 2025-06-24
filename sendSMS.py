import os
from twilio.rest import Client

def sendMSG(msg, ph_no) :
    account_sid = ""
    auth_token = ""
    client = Client(account_sid, auth_token)
    message = client.messages.create(
      body=msg,
      from_="+1762xxxx186",
      to=ph_no
    )
    return (message.sid)
  
