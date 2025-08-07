from fastapi import Depends
from fastapi.security import HTTPBearer

bearer_scheme = Depends(HTTPBearer())
