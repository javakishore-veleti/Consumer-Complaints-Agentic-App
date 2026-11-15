from pydantic import BaseModel, ConfigDict


class UpsertSecretResultOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    outcome: str


class UpsertSecretsOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: list[UpsertSecretResultOut]
