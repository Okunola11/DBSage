from fastapi import HTTPException, status
from sqlalchemy.orm import Session

def check_model_existence(db: Session, model, id):
    """Checks if a model instance exists by its ID

    Args:
        - db: the database session
        - model: the database model
        - id (str): the ID of the model instance to check

    Raises:
        HTTPException: 404 error if the model instance of the ID does not exist

    Returns:
        obj: the model instance
    """

    obj = db.get(model, ident=id)

    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} does not exist")

    return obj