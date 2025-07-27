from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()

# Enum for content type
class ContentTypeEnum(enum.Enum):
    assignment = "assignment"
    material = "material"

class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    image = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    role = Column(String, default="user")

    sessions = relationship("Session", back_populates="user", cascade="all, delete")
    accounts = relationship("Account", back_populates="user", cascade="all, delete")
    classes = relationship("Class", back_populates="teacher", cascade="all, delete")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete")


class Session(Base):
    __tablename__ = "session"

    id = Column(String, primary_key=True)
    expires_at = Column(DateTime, nullable=False)
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="sessions")


class Account(Base):
    __tablename__ = "account"

    id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    provider_id = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(String)
    refresh_token = Column(String)
    id_token = Column(String)
    access_token_expires_at = Column(DateTime)
    refresh_token_expires_at = Column(DateTime)
    scope = Column(String)
    password = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="accounts")


class Verification(Base):
    __tablename__ = "verification"

    id = Column(String, primary_key=True)
    identifier = Column(String, nullable=False)
    value = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Class(Base):
    __tablename__ = "classes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_name = Column(String, nullable=False)
    class_code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    teacher_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    active_start = Column(String, nullable=False)
    active_end = Column(String, nullable=False)

    teacher = relationship("User", back_populates="classes")
    enrollments = relationship("Enrollment", back_populates="class_", cascade="all, delete")
    contents = relationship("Content", back_populates="class_", cascade="all, delete")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    class_ = relationship("Class", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")


class Material(Base):
    __tablename__ = "materials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)

    contents = relationship("Content", back_populates="material", cascade="all, delete")


class Content(Base):
    __tablename__ = "contents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    material_id = Column(String, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(ContentTypeEnum), nullable=False)
    deadline = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    summary = Column(Text)

    class_ = relationship("Class", back_populates="contents")
    material = relationship("Material", back_populates="contents")
