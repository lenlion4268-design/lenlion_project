from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DeliveryStatus, PublicationStatus, PublishChannel


class PublishRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    volume_id: str | None = None
    title: str | None = Field(default=None, max_length=255)
    export_format: str = Field(default="markdown", alias="format")
    channel: PublishChannel = PublishChannel.LOCAL


class PublicationResponse(BaseModel):
    id: str
    project_id: str
    volume_id: str | None
    title: str
    format: str
    status: PublicationStatus
    storage_path: str
    chapter_count: int
    word_count: int
    channel: PublishChannel
    delivery_status: DeliveryStatus
    delivery_error: str | None
    external_ref: str | None
    created_at: datetime
    published_at: datetime | None

    model_config = {"from_attributes": True}


class PublicationListResponse(BaseModel):
    items: list[PublicationResponse]
    total: int
