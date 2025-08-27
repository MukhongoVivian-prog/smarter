# sms_utils.py
from africastalking.SMS import SMSService as SMS
from .config import AFRICASTALKING_USERNAME, AFRICASTALKING_API_KEY, AFRICASTALKING_SHORT_CODE

sms = SMS( username=AFRICASTALKING_USERNAME,
                        api_key=AFRICASTALKING_API_KEY)

# sms_utils.py
def send_sms(phone_number, message):
    try:
        response = sms.send(message=message, to=phone_number, from_=AFRICASTALKING_SHORT_CODE)
        return response
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return None