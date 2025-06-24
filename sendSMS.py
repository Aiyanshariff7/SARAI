import os
from twilio.rest import Client

def sendMSG(msg, ph_no) :
    account_sid = "ACcd9f88833ecd42eaaf34bd32da8c61097"
    auth_token = "e15061e67800ad9581e94ad804f24dc9e6"
    client = Client(account_sid, auth_token)
    message = client.messages.create(
      body=msg,
      from_="+1762xxxx186",
      to=ph_no
    )
    return (message.sid)
  