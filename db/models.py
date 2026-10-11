"""
SQLAlchemy Models for Scriptor Studio.
Persists screenplay/novel projects, acts, scenes, inspector metadata,
characters, and lore items in PostgreSQL.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, default="Proyecto Sin Título")
    logline = Column(Text, nullable=True)
    mode = Column(String(50), default="screenplay") # "screenplay" or "novel"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    acts = relationship("Act", back_populates="project", cascade="all, delete-orphan", order_by="Act.order_index")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.order_index")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    lore_items = relationship("LoreItem", back_populates="project", cascade="all, delete-orphan")


class Act(Base):
    __tablename__ = "acts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False, default="Nuevo Acto / Bloque")
    order_index = Column(Integer, default=0)

    project = relationship("Project", back_populates="acts")
    scenes = relationship("Scene", back_populates="act", order_by="Scene.order_index")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    act_id = Column(Integer, ForeignKey("acts.id"), nullable=True)
    scene_number = Column(Integer, default=1)
    title = Column(String(255), nullable=False, default="NUEVA ESCENA")
    content = Column(Text, nullable=False, default="")

    # Campos clave del Inspector (Análisis Dramático y Producción)
    synopsis = Column(Text, nullable=True, default="")
    character_goal = Column(Text, nullable=True, default="")
    conflict_obstacle = Column(Text, nullable=True, default="")
    revision_status = Column(String(100), default="⚪ Primer Borrador")
    time_of_day = Column(String(50), default="NOCHE")
    location = Column(String(255), default="")
    cast_members = Column(Text, default="")
    notes = Column(Text, default="")

    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="scenes")
    act = relationship("Act", back_populates="scenes")


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(150), nullable=False)
    role = Column(String(100), default="Protagonista")
    bio = Column(Text, default="")
    dramatic_need = Column(Text, default="")
    fatal_flaw = Column(Text, default="")
    dialogue_style = Column(Text, default="")
    arc = Column(Text, default="")

    project = relationship("Project", back_populates="characters")


class LoreItem(Base):
    __tablename__ = "lore_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="Investigación")
    content = Column(Text, default="")

    project = relationship("Project", back_populates="lore_items")
