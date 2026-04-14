from typing import Literal, Optional
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, model_validator


class SourceDefinition(BaseModel):
    source_id: str
    source_name: str
    db_type: Literal["mysql", "mariadb"] = "mysql"
    host: str
    port: int = 3306
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"
    timezone: str = "Asia/Shanghai"
    enabled: bool = True
    readonly: bool = True
    schema_version_hint: str = ""
    notes: str = ""


class SourcePublic(BaseModel):
    source_id: str
    source_name: str
    db_type: str
    host: str
    port: int
    database: str
    charset: str
    timezone: str
    enabled: bool
    readonly: bool
    schema_version_hint: str
    notes: str
    has_password: bool = Field(default=True)

    @classmethod
    def from_definition(cls, source: SourceDefinition) -> "SourcePublic":
        return cls(
            source_id=source.source_id,
            source_name=source.source_name,
            db_type=source.db_type,
            host=source.host,
            port=source.port,
            database=source.database,
            charset=source.charset,
            timezone=source.timezone,
            enabled=source.enabled,
            readonly=source.readonly,
            schema_version_hint=source.schema_version_hint,
            notes=source.notes,
            has_password=bool(source.password),
        )


class SourceConnectionTestRequest(BaseModel):
    source_id: str = "adhoc"
    source_name: str = "Adhoc Source"
    db_type: Literal["mysql", "mariadb"] = "mysql"
    host: str
    port: int = 3306
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"
    timezone: str = "Asia/Shanghai"
    readonly: bool = True

    def to_source_definition(self) -> SourceDefinition:
        return SourceDefinition(**self.model_dump())


class SourcePingResult(BaseModel):
    ok: bool
    source_id: str
    source_name: str
    message: str
    dsn_preview: str
    checks: dict[str, object] = Field(default_factory=dict)


class SourceImportUriRequest(BaseModel):
    source_name: str
    uri: str
    source_id: Optional[str] = None
    timezone: str = "Asia/Shanghai"

    def to_source_definition(self) -> SourceDefinition:
        parsed = urlparse(self.uri)
        query = parse_qs(parsed.query)
        db_type = "mysql"
        if parsed.scheme.startswith("mariadb"):
            db_type = "mariadb"
        charset = query.get("charset", ["utf8mb4"])[0]
        source_id = self.source_id or self.source_name.lower().replace(" ", "-")
        return SourceDefinition(
            source_id=source_id,
            source_name=self.source_name,
            db_type=db_type,
            host=parsed.hostname or "",
            port=parsed.port or 3306,
            user=parsed.username or "",
            password=parsed.password or "",
            database=(parsed.path or "").lstrip("/"),
            charset=charset,
            timezone=self.timezone,
        )


class SourceUpsertRequest(BaseModel):
    source_id: Optional[str] = None
    source_name: str
    db_type: Literal["mysql", "mariadb"] = "mysql"
    host: str
    port: int = 3306
    user: str
    password: Optional[str] = None
    database: str
    charset: str = "utf8mb4"
    timezone: str = "Asia/Shanghai"
    enabled: bool = True
    readonly: bool = True
    schema_version_hint: str = ""
    notes: str = ""

    @model_validator(mode="after")
    def fill_source_id(self) -> "SourceUpsertRequest":
        if not self.source_id:
            self.source_id = self.source_name.lower().strip().replace(" ", "-")
        return self

    def to_source_definition(
        self,
        *,
        existing: SourceDefinition | None = None,
        require_password: bool = True,
    ) -> SourceDefinition:
        password = self.password
        if not password and existing is not None:
            password = existing.password
        if require_password and not password:
            raise ValueError("password is required")
        return SourceDefinition(
            source_id=self.source_id or "",
            source_name=self.source_name,
            db_type=self.db_type,
            host=self.host,
            port=self.port,
            user=self.user,
            password=password or "",
            database=self.database,
            charset=self.charset,
            timezone=self.timezone,
            enabled=self.enabled,
            readonly=self.readonly,
            schema_version_hint=self.schema_version_hint,
            notes=self.notes,
        )
