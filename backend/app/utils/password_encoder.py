from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


async def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)
