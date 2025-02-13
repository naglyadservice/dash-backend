import bcrypt


class PasswordProcessor:
    def hash(self, password: str) -> str:
        encoded = password.encode("utf-8")
        salt = bcrypt.gensalt()

        return bcrypt.hashpw(encoded, salt).decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        plain_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")

        return bcrypt.checkpw(plain_bytes, hashed_bytes)
