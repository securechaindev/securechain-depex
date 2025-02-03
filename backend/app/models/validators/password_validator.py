from re import search


def validate_password(password):
    if len(password) < 8 or len(password) > 20:
        raise ValueError("the password mas been between 8 and 20 characters")
    if not search(r"[A-Z]", password):
        raise ValueError("the password must contain at least one capital letter")
    if not search(r"\d", password):
        raise ValueError("the password must contain at lest one digit")
    if not search(r"[\W_]", password):
        raise ValueError("the password must contain at least one special character")
    return password
