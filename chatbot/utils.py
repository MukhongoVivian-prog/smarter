from .role_responses import tenant_response, landlord_response, admin_response

def process_message(role, message, user=None):
    """
    Simple router to role-specific response functions.
    Extend this to call OpenAI/Rasa/etc. later.
    """
    role = (role or "").lower()
    if role == 'tenant':
        return tenant_response(message, user=user)
    if role == 'landlord':
        return landlord_response(message, user=user)
    if role == 'admin':
        return admin_response(message, user=user)
    # fallback
    return "I didn't understand that. Try 'help' or 'commands'."
