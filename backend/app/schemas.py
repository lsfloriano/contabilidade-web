from pydantic import BaseModel, ConfigDict


class ContaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nome: str
    natureza: str
    grupo: str
    tipo: str
