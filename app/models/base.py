from sqlmodel import SQLModel

from sqlalchemy.ext.declarative import declared_attr




class DbBase(SQLModel):
    @declared_attr
    def __tablename__(cls) -> str:
        return "".join(["_" + i.lower() if i.isupper() else i for i in cls.__name__]).lstrip("_")


