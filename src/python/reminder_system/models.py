from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, Date, ForeignKey, UniqueConstraint, ARRAY
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)
    middle_name = Column(Text)
    company_name = Column(Text)
    company_type = Column(Text)
    email = Column(Text)
    mobile = Column(BigInteger)
    gst_no = Column(Text)
    address = Column(String)
    # Relationships
    groups = relationship('ClientGroupMap', back_populates='client')
    reminders = relationship('ReminderInfo', back_populates='client')
    leads = relationship('Lead', back_populates='client')
    blocklists = relationship('ReminderBlocklist', back_populates='client')
    unsubscribes = relationship('ReminderUnsubscriber', back_populates='client')
    statuses = relationship('ReminderStatus', back_populates='client')

class ClientGroup(Base):
    __tablename__ = 'client_groups'
    group_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    group_code = Column(Text, unique=True, nullable=False)
    group_name = Column(Text, nullable=False)
    comments = Column(Text)
    # Relationships
    mappings = relationship('ClientGroupMap', back_populates='group')
    reminders = relationship('ReminderInfo', back_populates='group')

class ClientGroupMap(Base):
    __tablename__ = 'client_group_map'
    mapping_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    group_id = Column(BigInteger, ForeignKey('client_groups.group_id'))
    client_id = Column(BigInteger, ForeignKey('clients.id'))
    # Relationships
    group = relationship('ClientGroup', back_populates='mappings')
    client = relationship('Client', back_populates='groups')

class EmailTemplate(Base):
    __tablename__ = 'email_template'
    template_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    subject = Column(Text)
    body = Column(Text)
    external_reference_info = Column(Text)
    name = Column(Text, unique=True, nullable=False)
    data_references = Column(ARRAY(Text))
    # Relationships
    reminder_types = relationship('ReminderTypeInfo', back_populates='email_template')

class ReminderTypeInfo(Base):
    __tablename__ = 'reminder_type_info'
    reminder_type_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    email_template_id = Column(BigInteger, ForeignKey('email_template.template_id'), nullable=False)
    name = Column(Text, unique=True, nullable=False)
    # Relationships
    email_template = relationship('EmailTemplate', back_populates='reminder_types')
    reminders = relationship('ReminderInfo', back_populates='reminder_type')

class ReminderInfo(Base):
    __tablename__ = 'reminder_info'
    reminder_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reminder_type_id = Column(BigInteger, ForeignKey('reminder_type_info.reminder_type_id'), nullable=False)
    deadline = Column(Date, nullable=False)
    days_before_deadline = Column(ARRAY(Integer), nullable=False)
    client_id = Column(BigInteger, ForeignKey('clients.id'))
    group_id = Column(BigInteger, ForeignKey('client_groups.group_id'))
    # Relationships
    reminder_type = relationship('ReminderTypeInfo', back_populates='reminders')
    client = relationship('Client', back_populates='reminders')
    group = relationship('ClientGroup', back_populates='reminders')
    statuses = relationship('ReminderStatus', back_populates='reminder')
    unsubscribers = relationship('ReminderUnsubscriber', back_populates='reminder')

class ReminderStatus(Base):
    __tablename__ = 'reminder_status'
    request_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reminder_id = Column(BigInteger, ForeignKey('reminder_info.reminder_id'), nullable=False)
    client_id = Column(BigInteger, ForeignKey('clients.id'), nullable=False)
    status = Column(Text, nullable=False)
    error_message = Column(Text)
    # Relationships
    reminder = relationship('ReminderInfo', back_populates='statuses')
    client = relationship('Client', back_populates='statuses')

class ReminderBlocklist(Base):
    __tablename__ = 'reminder_blocklist'
    block_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    client_id = Column(BigInteger, ForeignKey('clients.id'), nullable=False)
    reason = Column(Text)
    # Relationships
    client = relationship('Client', back_populates='blocklists')

class ReminderUnsubscriber(Base):
    __tablename__ = 'reminder_unsubscribers'
    unsubscribe_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reminder_id = Column(BigInteger, ForeignKey('reminder_info.reminder_id'), nullable=False)
    client_id = Column(BigInteger, ForeignKey('clients.id'), nullable=False)
    reason_type = Column(Text)
    reason = Column(Text)
    # Relationships
    reminder = relationship('ReminderInfo', back_populates='unsubscribers')
    client = relationship('Client', back_populates='unsubscribes')

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    name = Column(Text, nullable=False)
    issue_description = Column(Text)
    mobile = Column(BigInteger)
    email = Column(Text)
    client_id = Column(BigInteger, ForeignKey('clients.id'))
    # Relationships
    client = relationship('Client', back_populates='leads')
