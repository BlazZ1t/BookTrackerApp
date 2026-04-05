from dataclasses import dataclass


@dataclass
class UserRecord:
    id: str
    username: str
    password_hash: str
