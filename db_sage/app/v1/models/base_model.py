from fastapi import Depends
from sqlalchemy import Column, String, ForeignKey, DateTime, func
from uuid_extensions import uuid7

from db_sage.app.db.database import Base

class BaseTableModel(Base):
    """Base model all other model inherits from

    Args:
        Base (_type_): base for sqlalchemy models
    """
    __abstract__ = True

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid7()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        obj_dict['id'] = self.id
        if self.created_at:
            obj_dict['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            obj_dict['updated_at'] = self.updated_at.isoformat()
        return obj_dict

    @classmethod
    def get_all(cls):
        """Returns all instance of the class in the db

        Returns:
            _type_: _description_
        """
        from api.db.database import get_db
        db = Depends(get_db)
        return db.query(cls).all()
    
    @classmethod
    def get_by_id(cls, id):
        """Returns a single object from the database

        Args:
            id (string): The ID of the object to be returned

        Returns:
            obj: single object
        """
        from api.db.database import get_db
        db = Depends(get_db)
        return db.query.filter_by(id=id).first()
