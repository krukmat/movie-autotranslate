from typing import List

from pydantic import BaseModel, Field


class UploadInitRequest(BaseModel):
    filename: str
    content_type: str = Field(alias="contentType")
    size: int


class UploadPart(BaseModel):
    part_number: int = Field(alias="partNumber")
    upload_url: str = Field(alias="uploadUrl")


class UploadInitResponse(BaseModel):
    asset_id: str = Field(alias="assetId")
    upload_id: str = Field(alias="uploadId")
    part_size: int = Field(alias="partSize")
    parts: List[UploadPart]


class UploadCompleteRequest(BaseModel):
    asset_id: str = Field(alias="assetId")
    upload_id: str = Field(alias="uploadId")
    etags: List[str]
    src_lang: str = Field(alias="srcLang")
    target_langs: List[str] = Field(alias="targetLangs")

