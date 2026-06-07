import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="TRUE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    probes: Mapped[list["Probe"]] = relationship(back_populates="target")


class Probe(Base):
    __tablename__ = "probes"
    __table_args__ = (PrimaryKeyConstraint("id", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rtt_ms: Mapped[float | None] = mapped_column(Float)
    packet_loss: Mapped[float | None] = mapped_column(Float)

    target: Mapped["Target"] = relationship(back_populates="probes")
    hops: Mapped[list["Hop"]] = relationship(
        back_populates="probe",
        primaryjoin="Probe.id == foreign(Hop.probe_id)",
    )


class Hop(Base):
    __tablename__ = "hops"
    __table_args__ = (PrimaryKeyConstraint("id", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    # No DB-level FK — TimescaleDB does not support FKs between hypertables
    probe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ttl: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45))
    rtt_ms: Mapped[float | None] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    city: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(255))
    asn: Mapped[str | None] = mapped_column(Text)

    probe: Mapped["Probe"] = relationship(
        back_populates="hops",
        primaryjoin="foreign(Hop.probe_id) == Probe.id",
    )