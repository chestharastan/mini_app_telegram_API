_contacts_by_user_id = {}


def save_telegram_contact(user_id, phone_number):
    if not user_id or not phone_number:
        return

    _contacts_by_user_id[str(user_id)] = phone_number


def get_telegram_contact(user_id):
    if not user_id:
        return None

    return _contacts_by_user_id.get(str(user_id))
