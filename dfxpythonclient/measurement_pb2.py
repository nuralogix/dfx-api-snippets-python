# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: measurement.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='measurement.proto',
  package='subscribe',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x11measurement.proto\x12\tsubscribe\"\x87\x01\n\x17SubscribeResultsRequest\x12>\n\x06Params\x18\x01 \x01(\x0b\x32..subscribe.SubscribeResultsRequest.ParamValues\x12\x11\n\tRequestID\x18\x02 \x01(\t\x1a\x19\n\x0bParamValues\x12\n\n\x02ID\x18\x01 \x01(\tb\x06proto3')
)




_SUBSCRIBERESULTSREQUEST_PARAMVALUES = _descriptor.Descriptor(
  name='ParamValues',
  full_name='subscribe.SubscribeResultsRequest.ParamValues',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ID', full_name='subscribe.SubscribeResultsRequest.ParamValues.ID', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=143,
  serialized_end=168,
)

_SUBSCRIBERESULTSREQUEST = _descriptor.Descriptor(
  name='SubscribeResultsRequest',
  full_name='subscribe.SubscribeResultsRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='Params', full_name='subscribe.SubscribeResultsRequest.Params', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='RequestID', full_name='subscribe.SubscribeResultsRequest.RequestID', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_SUBSCRIBERESULTSREQUEST_PARAMVALUES, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=33,
  serialized_end=168,
)

_SUBSCRIBERESULTSREQUEST_PARAMVALUES.containing_type = _SUBSCRIBERESULTSREQUEST
_SUBSCRIBERESULTSREQUEST.fields_by_name['Params'].message_type = _SUBSCRIBERESULTSREQUEST_PARAMVALUES
DESCRIPTOR.message_types_by_name['SubscribeResultsRequest'] = _SUBSCRIBERESULTSREQUEST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SubscribeResultsRequest = _reflection.GeneratedProtocolMessageType('SubscribeResultsRequest', (_message.Message,), dict(

  ParamValues = _reflection.GeneratedProtocolMessageType('ParamValues', (_message.Message,), dict(
    DESCRIPTOR = _SUBSCRIBERESULTSREQUEST_PARAMVALUES,
    __module__ = 'measurement_pb2'
    # @@protoc_insertion_point(class_scope:subscribe.SubscribeResultsRequest.ParamValues)
    ))
  ,
  DESCRIPTOR = _SUBSCRIBERESULTSREQUEST,
  __module__ = 'measurement_pb2'
  # @@protoc_insertion_point(class_scope:subscribe.SubscribeResultsRequest)
  ))
_sym_db.RegisterMessage(SubscribeResultsRequest)
_sym_db.RegisterMessage(SubscribeResultsRequest.ParamValues)


# @@protoc_insertion_point(module_scope)
