def tenant_response(message, user=None):
    txt = message.lower()
    if "find" in txt or "show" in txt or "available" in txt:
        return "Tell me where or what you’re looking for — e.g. '2-bedroom in Nairobi under 50k'."
    if "help" in txt or "commands" in txt:
        return "You can try: 'find 2-bedroom', 'my favorites', or 'how to apply'."
    return "I can help find properties, check favorites, or explain steps to apply."

def landlord_response(message, user=None):
    txt = message.lower()
    if "my properties" in txt or "listings" in txt:
        return "I can show your properties, stats, or new inquiries. Ask 'show my properties'."
    if "add property" in txt or "create listing" in txt:
        return "To add a property use the landlord dashboard or the 'Add Property' form."
    return "I can help with property management, viewing inquiries, and listing tips."

def admin_response(message, user=None):
    txt = message.lower()
    if "stats" in txt or "overview" in txt:
        return "I can show user counts, property counts, and recent reports. Ask 'show stats'."
    return "As admin you can manage users, listings, and review reports via the admin panel."
