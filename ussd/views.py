from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["POST", "GET"])
def ussd_callback(request):
    session_id = request.POST.get("sessionId", None)
    service_code = request.POST.get("serviceCode", None)
    phone_number = request.POST.get("phoneNumber", None)
    text = request.POST.get("text", "default")

    # Check if the user has selected an option
    if text == "":
        response = "CON Welcome to the USSD service.\n"
        response += "1. Confirm Booking \n"
        response += "2. Cancel your Booking\n"
        response += "3. Rate our services\n"
    elif text == "1":
        response = "CON Confirm your booking details\n"
        response += "Enter your booking ID: "
    elif text == "2":
        response = "CON Cancel your booking\n"
        response += "Enter your booking ID: "
    elif text == "3":
        response = "CON Rate our services\n"
        response += "1. Excellent\n"
        response += "2. Good\n"
        response += "3. Fair\n"
        response += "4. Poor\n"
    else:
        response = "END Invalid option. Please try again."

    return HttpResponse(response)