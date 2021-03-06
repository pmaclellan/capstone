# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: control_signals.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='control_signals.proto',
  package='',
  syntax='proto3',
  serialized_pb=_b('\n\x15\x63ontrol_signals.proto\"O\n\x0cStartRequest\x12\x0c\n\x04port\x18\x01 \x01(\r\x12\x10\n\x08\x63hannels\x18\x02 \x01(\r\x12\x0c\n\x04rate\x18\x03 \x01(\r\x12\x11\n\ttimestamp\x18\x04 \x01(\x04\"-\n\x0bStopRequest\x12\x0c\n\x04port\x18\x01 \x01(\r\x12\x10\n\x08\x63hannels\x18\x02 \x01(\r\"j\n\x12SensitivityRequest\x12,\n\x07voltage\x18\x01 \x01(\x0e\x32\x1b.SensitivityRequest.Voltage\"&\n\x07Voltage\x12\x08\n\x04\x46IVE\x10\x00\x12\x07\n\x03TEN\x10\x01\x12\x08\n\x04VREF\x10\x02\"\x8c\x01\n\x0eRequestWrapper\x12\x10\n\x08sequence\x18\x01 \x01(\r\x12\x1e\n\x05start\x18\x02 \x01(\x0b\x32\r.StartRequestH\x00\x12\x1c\n\x04stop\x18\x03 \x01(\x0b\x32\x0c.StopRequestH\x00\x12#\n\x04sens\x18\x04 \x01(\x0b\x32\x13.SensitivityRequestH\x00\x42\x05\n\x03msgb\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_SENSITIVITYREQUEST_VOLTAGE = _descriptor.EnumDescriptor(
  name='Voltage',
  full_name='SensitivityRequest.Voltage',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='FIVE', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='TEN', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='VREF', index=2, number=2,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=221,
  serialized_end=259,
)
_sym_db.RegisterEnumDescriptor(_SENSITIVITYREQUEST_VOLTAGE)


_STARTREQUEST = _descriptor.Descriptor(
  name='StartRequest',
  full_name='StartRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='port', full_name='StartRequest.port', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='channels', full_name='StartRequest.channels', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='rate', full_name='StartRequest.rate', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='StartRequest.timestamp', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=25,
  serialized_end=104,
)


_STOPREQUEST = _descriptor.Descriptor(
  name='StopRequest',
  full_name='StopRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='port', full_name='StopRequest.port', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='channels', full_name='StopRequest.channels', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=106,
  serialized_end=151,
)


_SENSITIVITYREQUEST = _descriptor.Descriptor(
  name='SensitivityRequest',
  full_name='SensitivityRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='voltage', full_name='SensitivityRequest.voltage', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _SENSITIVITYREQUEST_VOLTAGE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=153,
  serialized_end=259,
)


_REQUESTWRAPPER = _descriptor.Descriptor(
  name='RequestWrapper',
  full_name='RequestWrapper',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='sequence', full_name='RequestWrapper.sequence', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='start', full_name='RequestWrapper.start', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='stop', full_name='RequestWrapper.stop', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sens', full_name='RequestWrapper.sens', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='msg', full_name='RequestWrapper.msg',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=262,
  serialized_end=402,
)

_SENSITIVITYREQUEST.fields_by_name['voltage'].enum_type = _SENSITIVITYREQUEST_VOLTAGE
_SENSITIVITYREQUEST_VOLTAGE.containing_type = _SENSITIVITYREQUEST
_REQUESTWRAPPER.fields_by_name['start'].message_type = _STARTREQUEST
_REQUESTWRAPPER.fields_by_name['stop'].message_type = _STOPREQUEST
_REQUESTWRAPPER.fields_by_name['sens'].message_type = _SENSITIVITYREQUEST
_REQUESTWRAPPER.oneofs_by_name['msg'].fields.append(
  _REQUESTWRAPPER.fields_by_name['start'])
_REQUESTWRAPPER.fields_by_name['start'].containing_oneof = _REQUESTWRAPPER.oneofs_by_name['msg']
_REQUESTWRAPPER.oneofs_by_name['msg'].fields.append(
  _REQUESTWRAPPER.fields_by_name['stop'])
_REQUESTWRAPPER.fields_by_name['stop'].containing_oneof = _REQUESTWRAPPER.oneofs_by_name['msg']
_REQUESTWRAPPER.oneofs_by_name['msg'].fields.append(
  _REQUESTWRAPPER.fields_by_name['sens'])
_REQUESTWRAPPER.fields_by_name['sens'].containing_oneof = _REQUESTWRAPPER.oneofs_by_name['msg']
DESCRIPTOR.message_types_by_name['StartRequest'] = _STARTREQUEST
DESCRIPTOR.message_types_by_name['StopRequest'] = _STOPREQUEST
DESCRIPTOR.message_types_by_name['SensitivityRequest'] = _SENSITIVITYREQUEST
DESCRIPTOR.message_types_by_name['RequestWrapper'] = _REQUESTWRAPPER

StartRequest = _reflection.GeneratedProtocolMessageType('StartRequest', (_message.Message,), dict(
  DESCRIPTOR = _STARTREQUEST,
  __module__ = 'control_signals_pb2'
  # @@protoc_insertion_point(class_scope:StartRequest)
  ))
_sym_db.RegisterMessage(StartRequest)

StopRequest = _reflection.GeneratedProtocolMessageType('StopRequest', (_message.Message,), dict(
  DESCRIPTOR = _STOPREQUEST,
  __module__ = 'control_signals_pb2'
  # @@protoc_insertion_point(class_scope:StopRequest)
  ))
_sym_db.RegisterMessage(StopRequest)

SensitivityRequest = _reflection.GeneratedProtocolMessageType('SensitivityRequest', (_message.Message,), dict(
  DESCRIPTOR = _SENSITIVITYREQUEST,
  __module__ = 'control_signals_pb2'
  # @@protoc_insertion_point(class_scope:SensitivityRequest)
  ))
_sym_db.RegisterMessage(SensitivityRequest)

RequestWrapper = _reflection.GeneratedProtocolMessageType('RequestWrapper', (_message.Message,), dict(
  DESCRIPTOR = _REQUESTWRAPPER,
  __module__ = 'control_signals_pb2'
  # @@protoc_insertion_point(class_scope:RequestWrapper)
  ))
_sym_db.RegisterMessage(RequestWrapper)


# @@protoc_insertion_point(module_scope)
