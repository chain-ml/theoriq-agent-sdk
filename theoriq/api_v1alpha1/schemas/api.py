from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class PublicKeyResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    public_key: str
    key_type: str
