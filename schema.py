from pydantic import BaseModel
from datetime import datetime

class Chat(BaseModel):
    sender : str
    reciever: str
    msg : str
    created_at : datetime | None
