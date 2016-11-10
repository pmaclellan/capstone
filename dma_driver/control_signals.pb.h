// Generated by the protocol buffer compiler.  DO NOT EDIT!
// source: control_signals.proto

#ifndef PROTOBUF_control_5fsignals_2eproto__INCLUDED
#define PROTOBUF_control_5fsignals_2eproto__INCLUDED

#include <string>

#include <google/protobuf/stubs/common.h>

#if GOOGLE_PROTOBUF_VERSION < 3001000
#error This file was generated by a newer version of protoc which is
#error incompatible with your Protocol Buffer headers.  Please update
#error your headers.
#endif
#if 3001000 < GOOGLE_PROTOBUF_MIN_PROTOC_VERSION
#error This file was generated by an older version of protoc which is
#error incompatible with your Protocol Buffer headers.  Please
#error regenerate this file with a newer version of protoc.
#endif

#include <google/protobuf/arena.h>
#include <google/protobuf/arenastring.h>
#include <google/protobuf/generated_message_util.h>
#include <google/protobuf/metadata.h>
#include <google/protobuf/message.h>
#include <google/protobuf/repeated_field.h>
#include <google/protobuf/extension_set.h>
#include <google/protobuf/generated_enum_reflection.h>
#include <google/protobuf/unknown_field_set.h>
// @@protoc_insertion_point(includes)

// Internal implementation detail -- do not call these.
void protobuf_AddDesc_control_5fsignals_2eproto();
void protobuf_InitDefaults_control_5fsignals_2eproto();
void protobuf_AssignDesc_control_5fsignals_2eproto();
void protobuf_ShutdownFile_control_5fsignals_2eproto();

class RequestWrapper;
class SampleRateRequest;
class SensitivityRequest;
class StartRequest;
class StopRequest;

enum SensitivityRequest_Voltage {
  SensitivityRequest_Voltage_FIVE = 0,
  SensitivityRequest_Voltage_TEN = 1,
  SensitivityRequest_Voltage_VREF = 2,
  SensitivityRequest_Voltage_SensitivityRequest_Voltage_INT_MIN_SENTINEL_DO_NOT_USE_ = ::google::protobuf::kint32min,
  SensitivityRequest_Voltage_SensitivityRequest_Voltage_INT_MAX_SENTINEL_DO_NOT_USE_ = ::google::protobuf::kint32max
};
bool SensitivityRequest_Voltage_IsValid(int value);
const SensitivityRequest_Voltage SensitivityRequest_Voltage_Voltage_MIN = SensitivityRequest_Voltage_FIVE;
const SensitivityRequest_Voltage SensitivityRequest_Voltage_Voltage_MAX = SensitivityRequest_Voltage_VREF;
const int SensitivityRequest_Voltage_Voltage_ARRAYSIZE = SensitivityRequest_Voltage_Voltage_MAX + 1;

const ::google::protobuf::EnumDescriptor* SensitivityRequest_Voltage_descriptor();
inline const ::std::string& SensitivityRequest_Voltage_Name(SensitivityRequest_Voltage value) {
  return ::google::protobuf::internal::NameOfEnum(
    SensitivityRequest_Voltage_descriptor(), value);
}
inline bool SensitivityRequest_Voltage_Parse(
    const ::std::string& name, SensitivityRequest_Voltage* value) {
  return ::google::protobuf::internal::ParseNamedEnum<SensitivityRequest_Voltage>(
    SensitivityRequest_Voltage_descriptor(), name, value);
}
// ===================================================================

class StartRequest : public ::google::protobuf::Message /* @@protoc_insertion_point(class_definition:StartRequest) */ {
 public:
  StartRequest();
  virtual ~StartRequest();

  StartRequest(const StartRequest& from);

  inline StartRequest& operator=(const StartRequest& from) {
    CopyFrom(from);
    return *this;
  }

  static const ::google::protobuf::Descriptor* descriptor();
  static const StartRequest& default_instance();

  static const StartRequest* internal_default_instance();

  void Swap(StartRequest* other);

  // implements Message ----------------------------------------------

  inline StartRequest* New() const { return New(NULL); }

  StartRequest* New(::google::protobuf::Arena* arena) const;
  void CopyFrom(const ::google::protobuf::Message& from);
  void MergeFrom(const ::google::protobuf::Message& from);
  void CopyFrom(const StartRequest& from);
  void MergeFrom(const StartRequest& from);
  void Clear();
  bool IsInitialized() const;

  size_t ByteSizeLong() const;
  bool MergePartialFromCodedStream(
      ::google::protobuf::io::CodedInputStream* input);
  void SerializeWithCachedSizes(
      ::google::protobuf::io::CodedOutputStream* output) const;
  ::google::protobuf::uint8* InternalSerializeWithCachedSizesToArray(
      bool deterministic, ::google::protobuf::uint8* output) const;
  ::google::protobuf::uint8* SerializeWithCachedSizesToArray(::google::protobuf::uint8* output) const {
    return InternalSerializeWithCachedSizesToArray(false, output);
  }
  int GetCachedSize() const { return _cached_size_; }
  private:
  void SharedCtor();
  void SharedDtor();
  void SetCachedSize(int size) const;
  void InternalSwap(StartRequest* other);
  void UnsafeMergeFrom(const StartRequest& from);
  private:
  inline ::google::protobuf::Arena* GetArenaNoVirtual() const {
    return _internal_metadata_.arena();
  }
  inline void* MaybeArenaPtr() const {
    return _internal_metadata_.raw_arena_ptr();
  }
  public:

  ::google::protobuf::Metadata GetMetadata() const;

  // nested types ----------------------------------------------------

  // accessors -------------------------------------------------------

  // optional uint32 port = 1;
  void clear_port();
  static const int kPortFieldNumber = 1;
  ::google::protobuf::uint32 port() const;
  void set_port(::google::protobuf::uint32 value);

  // optional uint32 channels = 2;
  void clear_channels();
  static const int kChannelsFieldNumber = 2;
  ::google::protobuf::uint32 channels() const;
  void set_channels(::google::protobuf::uint32 value);

  // @@protoc_insertion_point(class_scope:StartRequest)
 private:

  ::google::protobuf::internal::InternalMetadataWithArena _internal_metadata_;
  ::google::protobuf::uint32 port_;
  ::google::protobuf::uint32 channels_;
  mutable int _cached_size_;
  friend void  protobuf_InitDefaults_control_5fsignals_2eproto_impl();
  friend void  protobuf_AddDesc_control_5fsignals_2eproto_impl();
  friend void protobuf_AssignDesc_control_5fsignals_2eproto();
  friend void protobuf_ShutdownFile_control_5fsignals_2eproto();

  void InitAsDefaultInstance();
};
extern ::google::protobuf::internal::ExplicitlyConstructed<StartRequest> StartRequest_default_instance_;

// -------------------------------------------------------------------

class StopRequest : public ::google::protobuf::Message /* @@protoc_insertion_point(class_definition:StopRequest) */ {
 public:
  StopRequest();
  virtual ~StopRequest();

  StopRequest(const StopRequest& from);

  inline StopRequest& operator=(const StopRequest& from) {
    CopyFrom(from);
    return *this;
  }

  static const ::google::protobuf::Descriptor* descriptor();
  static const StopRequest& default_instance();

  static const StopRequest* internal_default_instance();

  void Swap(StopRequest* other);

  // implements Message ----------------------------------------------

  inline StopRequest* New() const { return New(NULL); }

  StopRequest* New(::google::protobuf::Arena* arena) const;
  void CopyFrom(const ::google::protobuf::Message& from);
  void MergeFrom(const ::google::protobuf::Message& from);
  void CopyFrom(const StopRequest& from);
  void MergeFrom(const StopRequest& from);
  void Clear();
  bool IsInitialized() const;

  size_t ByteSizeLong() const;
  bool MergePartialFromCodedStream(
      ::google::protobuf::io::CodedInputStream* input);
  void SerializeWithCachedSizes(
      ::google::protobuf::io::CodedOutputStream* output) const;
  ::google::protobuf::uint8* InternalSerializeWithCachedSizesToArray(
      bool deterministic, ::google::protobuf::uint8* output) const;
  ::google::protobuf::uint8* SerializeWithCachedSizesToArray(::google::protobuf::uint8* output) const {
    return InternalSerializeWithCachedSizesToArray(false, output);
  }
  int GetCachedSize() const { return _cached_size_; }
  private:
  void SharedCtor();
  void SharedDtor();
  void SetCachedSize(int size) const;
  void InternalSwap(StopRequest* other);
  void UnsafeMergeFrom(const StopRequest& from);
  private:
  inline ::google::protobuf::Arena* GetArenaNoVirtual() const {
    return _internal_metadata_.arena();
  }
  inline void* MaybeArenaPtr() const {
    return _internal_metadata_.raw_arena_ptr();
  }
  public:

  ::google::protobuf::Metadata GetMetadata() const;

  // nested types ----------------------------------------------------

  // accessors -------------------------------------------------------

  // optional uint32 port = 1;
  void clear_port();
  static const int kPortFieldNumber = 1;
  ::google::protobuf::uint32 port() const;
  void set_port(::google::protobuf::uint32 value);

  // optional uint32 channels = 2;
  void clear_channels();
  static const int kChannelsFieldNumber = 2;
  ::google::protobuf::uint32 channels() const;
  void set_channels(::google::protobuf::uint32 value);

  // @@protoc_insertion_point(class_scope:StopRequest)
 private:

  ::google::protobuf::internal::InternalMetadataWithArena _internal_metadata_;
  ::google::protobuf::uint32 port_;
  ::google::protobuf::uint32 channels_;
  mutable int _cached_size_;
  friend void  protobuf_InitDefaults_control_5fsignals_2eproto_impl();
  friend void  protobuf_AddDesc_control_5fsignals_2eproto_impl();
  friend void protobuf_AssignDesc_control_5fsignals_2eproto();
  friend void protobuf_ShutdownFile_control_5fsignals_2eproto();

  void InitAsDefaultInstance();
};
extern ::google::protobuf::internal::ExplicitlyConstructed<StopRequest> StopRequest_default_instance_;

// -------------------------------------------------------------------

class SampleRateRequest : public ::google::protobuf::Message /* @@protoc_insertion_point(class_definition:SampleRateRequest) */ {
 public:
  SampleRateRequest();
  virtual ~SampleRateRequest();

  SampleRateRequest(const SampleRateRequest& from);

  inline SampleRateRequest& operator=(const SampleRateRequest& from) {
    CopyFrom(from);
    return *this;
  }

  static const ::google::protobuf::Descriptor* descriptor();
  static const SampleRateRequest& default_instance();

  static const SampleRateRequest* internal_default_instance();

  void Swap(SampleRateRequest* other);

  // implements Message ----------------------------------------------

  inline SampleRateRequest* New() const { return New(NULL); }

  SampleRateRequest* New(::google::protobuf::Arena* arena) const;
  void CopyFrom(const ::google::protobuf::Message& from);
  void MergeFrom(const ::google::protobuf::Message& from);
  void CopyFrom(const SampleRateRequest& from);
  void MergeFrom(const SampleRateRequest& from);
  void Clear();
  bool IsInitialized() const;

  size_t ByteSizeLong() const;
  bool MergePartialFromCodedStream(
      ::google::protobuf::io::CodedInputStream* input);
  void SerializeWithCachedSizes(
      ::google::protobuf::io::CodedOutputStream* output) const;
  ::google::protobuf::uint8* InternalSerializeWithCachedSizesToArray(
      bool deterministic, ::google::protobuf::uint8* output) const;
  ::google::protobuf::uint8* SerializeWithCachedSizesToArray(::google::protobuf::uint8* output) const {
    return InternalSerializeWithCachedSizesToArray(false, output);
  }
  int GetCachedSize() const { return _cached_size_; }
  private:
  void SharedCtor();
  void SharedDtor();
  void SetCachedSize(int size) const;
  void InternalSwap(SampleRateRequest* other);
  void UnsafeMergeFrom(const SampleRateRequest& from);
  private:
  inline ::google::protobuf::Arena* GetArenaNoVirtual() const {
    return _internal_metadata_.arena();
  }
  inline void* MaybeArenaPtr() const {
    return _internal_metadata_.raw_arena_ptr();
  }
  public:

  ::google::protobuf::Metadata GetMetadata() const;

  // nested types ----------------------------------------------------

  // accessors -------------------------------------------------------

  // optional uint32 rate = 1;
  void clear_rate();
  static const int kRateFieldNumber = 1;
  ::google::protobuf::uint32 rate() const;
  void set_rate(::google::protobuf::uint32 value);

  // @@protoc_insertion_point(class_scope:SampleRateRequest)
 private:

  ::google::protobuf::internal::InternalMetadataWithArena _internal_metadata_;
  ::google::protobuf::uint32 rate_;
  mutable int _cached_size_;
  friend void  protobuf_InitDefaults_control_5fsignals_2eproto_impl();
  friend void  protobuf_AddDesc_control_5fsignals_2eproto_impl();
  friend void protobuf_AssignDesc_control_5fsignals_2eproto();
  friend void protobuf_ShutdownFile_control_5fsignals_2eproto();

  void InitAsDefaultInstance();
};
extern ::google::protobuf::internal::ExplicitlyConstructed<SampleRateRequest> SampleRateRequest_default_instance_;

// -------------------------------------------------------------------

class SensitivityRequest : public ::google::protobuf::Message /* @@protoc_insertion_point(class_definition:SensitivityRequest) */ {
 public:
  SensitivityRequest();
  virtual ~SensitivityRequest();

  SensitivityRequest(const SensitivityRequest& from);

  inline SensitivityRequest& operator=(const SensitivityRequest& from) {
    CopyFrom(from);
    return *this;
  }

  static const ::google::protobuf::Descriptor* descriptor();
  static const SensitivityRequest& default_instance();

  static const SensitivityRequest* internal_default_instance();

  void Swap(SensitivityRequest* other);

  // implements Message ----------------------------------------------

  inline SensitivityRequest* New() const { return New(NULL); }

  SensitivityRequest* New(::google::protobuf::Arena* arena) const;
  void CopyFrom(const ::google::protobuf::Message& from);
  void MergeFrom(const ::google::protobuf::Message& from);
  void CopyFrom(const SensitivityRequest& from);
  void MergeFrom(const SensitivityRequest& from);
  void Clear();
  bool IsInitialized() const;

  size_t ByteSizeLong() const;
  bool MergePartialFromCodedStream(
      ::google::protobuf::io::CodedInputStream* input);
  void SerializeWithCachedSizes(
      ::google::protobuf::io::CodedOutputStream* output) const;
  ::google::protobuf::uint8* InternalSerializeWithCachedSizesToArray(
      bool deterministic, ::google::protobuf::uint8* output) const;
  ::google::protobuf::uint8* SerializeWithCachedSizesToArray(::google::protobuf::uint8* output) const {
    return InternalSerializeWithCachedSizesToArray(false, output);
  }
  int GetCachedSize() const { return _cached_size_; }
  private:
  void SharedCtor();
  void SharedDtor();
  void SetCachedSize(int size) const;
  void InternalSwap(SensitivityRequest* other);
  void UnsafeMergeFrom(const SensitivityRequest& from);
  private:
  inline ::google::protobuf::Arena* GetArenaNoVirtual() const {
    return _internal_metadata_.arena();
  }
  inline void* MaybeArenaPtr() const {
    return _internal_metadata_.raw_arena_ptr();
  }
  public:

  ::google::protobuf::Metadata GetMetadata() const;

  // nested types ----------------------------------------------------

  typedef SensitivityRequest_Voltage Voltage;
  static const Voltage FIVE =
    SensitivityRequest_Voltage_FIVE;
  static const Voltage TEN =
    SensitivityRequest_Voltage_TEN;
  static const Voltage VREF =
    SensitivityRequest_Voltage_VREF;
  static inline bool Voltage_IsValid(int value) {
    return SensitivityRequest_Voltage_IsValid(value);
  }
  static const Voltage Voltage_MIN =
    SensitivityRequest_Voltage_Voltage_MIN;
  static const Voltage Voltage_MAX =
    SensitivityRequest_Voltage_Voltage_MAX;
  static const int Voltage_ARRAYSIZE =
    SensitivityRequest_Voltage_Voltage_ARRAYSIZE;
  static inline const ::google::protobuf::EnumDescriptor*
  Voltage_descriptor() {
    return SensitivityRequest_Voltage_descriptor();
  }
  static inline const ::std::string& Voltage_Name(Voltage value) {
    return SensitivityRequest_Voltage_Name(value);
  }
  static inline bool Voltage_Parse(const ::std::string& name,
      Voltage* value) {
    return SensitivityRequest_Voltage_Parse(name, value);
  }

  // accessors -------------------------------------------------------

  // optional .SensitivityRequest.Voltage voltage = 1;
  void clear_voltage();
  static const int kVoltageFieldNumber = 1;
  ::SensitivityRequest_Voltage voltage() const;
  void set_voltage(::SensitivityRequest_Voltage value);

  // @@protoc_insertion_point(class_scope:SensitivityRequest)
 private:

  ::google::protobuf::internal::InternalMetadataWithArena _internal_metadata_;
  int voltage_;
  mutable int _cached_size_;
  friend void  protobuf_InitDefaults_control_5fsignals_2eproto_impl();
  friend void  protobuf_AddDesc_control_5fsignals_2eproto_impl();
  friend void protobuf_AssignDesc_control_5fsignals_2eproto();
  friend void protobuf_ShutdownFile_control_5fsignals_2eproto();

  void InitAsDefaultInstance();
};
extern ::google::protobuf::internal::ExplicitlyConstructed<SensitivityRequest> SensitivityRequest_default_instance_;

// -------------------------------------------------------------------

class RequestWrapper : public ::google::protobuf::Message /* @@protoc_insertion_point(class_definition:RequestWrapper) */ {
 public:
  RequestWrapper();
  virtual ~RequestWrapper();

  RequestWrapper(const RequestWrapper& from);

  inline RequestWrapper& operator=(const RequestWrapper& from) {
    CopyFrom(from);
    return *this;
  }

  static const ::google::protobuf::Descriptor* descriptor();
  static const RequestWrapper& default_instance();

  enum MsgCase {
    kStart = 2,
    kStop = 3,
    kRate = 4,
    kSens = 5,
    MSG_NOT_SET = 0,
  };

  static const RequestWrapper* internal_default_instance();

  void Swap(RequestWrapper* other);

  // implements Message ----------------------------------------------

  inline RequestWrapper* New() const { return New(NULL); }

  RequestWrapper* New(::google::protobuf::Arena* arena) const;
  void CopyFrom(const ::google::protobuf::Message& from);
  void MergeFrom(const ::google::protobuf::Message& from);
  void CopyFrom(const RequestWrapper& from);
  void MergeFrom(const RequestWrapper& from);
  void Clear();
  bool IsInitialized() const;

  size_t ByteSizeLong() const;
  bool MergePartialFromCodedStream(
      ::google::protobuf::io::CodedInputStream* input);
  void SerializeWithCachedSizes(
      ::google::protobuf::io::CodedOutputStream* output) const;
  ::google::protobuf::uint8* InternalSerializeWithCachedSizesToArray(
      bool deterministic, ::google::protobuf::uint8* output) const;
  ::google::protobuf::uint8* SerializeWithCachedSizesToArray(::google::protobuf::uint8* output) const {
    return InternalSerializeWithCachedSizesToArray(false, output);
  }
  int GetCachedSize() const { return _cached_size_; }
  private:
  void SharedCtor();
  void SharedDtor();
  void SetCachedSize(int size) const;
  void InternalSwap(RequestWrapper* other);
  void UnsafeMergeFrom(const RequestWrapper& from);
  private:
  inline ::google::protobuf::Arena* GetArenaNoVirtual() const {
    return _internal_metadata_.arena();
  }
  inline void* MaybeArenaPtr() const {
    return _internal_metadata_.raw_arena_ptr();
  }
  public:

  ::google::protobuf::Metadata GetMetadata() const;

  // nested types ----------------------------------------------------

  // accessors -------------------------------------------------------

  // optional uint32 sequence = 1;
  void clear_sequence();
  static const int kSequenceFieldNumber = 1;
  ::google::protobuf::uint32 sequence() const;
  void set_sequence(::google::protobuf::uint32 value);

  // optional .StartRequest start = 2;
  bool has_start() const;
  void clear_start();
  static const int kStartFieldNumber = 2;
  const ::StartRequest& start() const;
  ::StartRequest* mutable_start();
  ::StartRequest* release_start();
  void set_allocated_start(::StartRequest* start);

  // optional .StopRequest stop = 3;
  bool has_stop() const;
  void clear_stop();
  static const int kStopFieldNumber = 3;
  const ::StopRequest& stop() const;
  ::StopRequest* mutable_stop();
  ::StopRequest* release_stop();
  void set_allocated_stop(::StopRequest* stop);

  // optional .SampleRateRequest rate = 4;
  bool has_rate() const;
  void clear_rate();
  static const int kRateFieldNumber = 4;
  const ::SampleRateRequest& rate() const;
  ::SampleRateRequest* mutable_rate();
  ::SampleRateRequest* release_rate();
  void set_allocated_rate(::SampleRateRequest* rate);

  // optional .SensitivityRequest sens = 5;
  bool has_sens() const;
  void clear_sens();
  static const int kSensFieldNumber = 5;
  const ::SensitivityRequest& sens() const;
  ::SensitivityRequest* mutable_sens();
  ::SensitivityRequest* release_sens();
  void set_allocated_sens(::SensitivityRequest* sens);

  MsgCase msg_case() const;
  // @@protoc_insertion_point(class_scope:RequestWrapper)
 private:
  inline void set_has_start();
  inline void set_has_stop();
  inline void set_has_rate();
  inline void set_has_sens();

  inline bool has_msg() const;
  void clear_msg();
  inline void clear_has_msg();

  ::google::protobuf::internal::InternalMetadataWithArena _internal_metadata_;
  ::google::protobuf::uint32 sequence_;
  union MsgUnion {
    MsgUnion() {}
    ::StartRequest* start_;
    ::StopRequest* stop_;
    ::SampleRateRequest* rate_;
    ::SensitivityRequest* sens_;
  } msg_;
  mutable int _cached_size_;
  ::google::protobuf::uint32 _oneof_case_[1];

  friend void  protobuf_InitDefaults_control_5fsignals_2eproto_impl();
  friend void  protobuf_AddDesc_control_5fsignals_2eproto_impl();
  friend void protobuf_AssignDesc_control_5fsignals_2eproto();
  friend void protobuf_ShutdownFile_control_5fsignals_2eproto();

  void InitAsDefaultInstance();
};
extern ::google::protobuf::internal::ExplicitlyConstructed<RequestWrapper> RequestWrapper_default_instance_;

// ===================================================================


// ===================================================================

#if !PROTOBUF_INLINE_NOT_IN_HEADERS
// StartRequest

// optional uint32 port = 1;
inline void StartRequest::clear_port() {
  port_ = 0u;
}
inline ::google::protobuf::uint32 StartRequest::port() const {
  // @@protoc_insertion_point(field_get:StartRequest.port)
  return port_;
}
inline void StartRequest::set_port(::google::protobuf::uint32 value) {
  
  port_ = value;
  // @@protoc_insertion_point(field_set:StartRequest.port)
}

// optional uint32 channels = 2;
inline void StartRequest::clear_channels() {
  channels_ = 0u;
}
inline ::google::protobuf::uint32 StartRequest::channels() const {
  // @@protoc_insertion_point(field_get:StartRequest.channels)
  return channels_;
}
inline void StartRequest::set_channels(::google::protobuf::uint32 value) {
  
  channels_ = value;
  // @@protoc_insertion_point(field_set:StartRequest.channels)
}

inline const StartRequest* StartRequest::internal_default_instance() {
  return &StartRequest_default_instance_.get();
}
// -------------------------------------------------------------------

// StopRequest

// optional uint32 port = 1;
inline void StopRequest::clear_port() {
  port_ = 0u;
}
inline ::google::protobuf::uint32 StopRequest::port() const {
  // @@protoc_insertion_point(field_get:StopRequest.port)
  return port_;
}
inline void StopRequest::set_port(::google::protobuf::uint32 value) {
  
  port_ = value;
  // @@protoc_insertion_point(field_set:StopRequest.port)
}

// optional uint32 channels = 2;
inline void StopRequest::clear_channels() {
  channels_ = 0u;
}
inline ::google::protobuf::uint32 StopRequest::channels() const {
  // @@protoc_insertion_point(field_get:StopRequest.channels)
  return channels_;
}
inline void StopRequest::set_channels(::google::protobuf::uint32 value) {
  
  channels_ = value;
  // @@protoc_insertion_point(field_set:StopRequest.channels)
}

inline const StopRequest* StopRequest::internal_default_instance() {
  return &StopRequest_default_instance_.get();
}
// -------------------------------------------------------------------

// SampleRateRequest

// optional uint32 rate = 1;
inline void SampleRateRequest::clear_rate() {
  rate_ = 0u;
}
inline ::google::protobuf::uint32 SampleRateRequest::rate() const {
  // @@protoc_insertion_point(field_get:SampleRateRequest.rate)
  return rate_;
}
inline void SampleRateRequest::set_rate(::google::protobuf::uint32 value) {
  
  rate_ = value;
  // @@protoc_insertion_point(field_set:SampleRateRequest.rate)
}

inline const SampleRateRequest* SampleRateRequest::internal_default_instance() {
  return &SampleRateRequest_default_instance_.get();
}
// -------------------------------------------------------------------

// SensitivityRequest

// optional .SensitivityRequest.Voltage voltage = 1;
inline void SensitivityRequest::clear_voltage() {
  voltage_ = 0;
}
inline ::SensitivityRequest_Voltage SensitivityRequest::voltage() const {
  // @@protoc_insertion_point(field_get:SensitivityRequest.voltage)
  return static_cast< ::SensitivityRequest_Voltage >(voltage_);
}
inline void SensitivityRequest::set_voltage(::SensitivityRequest_Voltage value) {
  
  voltage_ = value;
  // @@protoc_insertion_point(field_set:SensitivityRequest.voltage)
}

inline const SensitivityRequest* SensitivityRequest::internal_default_instance() {
  return &SensitivityRequest_default_instance_.get();
}
// -------------------------------------------------------------------

// RequestWrapper

// optional uint32 sequence = 1;
inline void RequestWrapper::clear_sequence() {
  sequence_ = 0u;
}
inline ::google::protobuf::uint32 RequestWrapper::sequence() const {
  // @@protoc_insertion_point(field_get:RequestWrapper.sequence)
  return sequence_;
}
inline void RequestWrapper::set_sequence(::google::protobuf::uint32 value) {
  
  sequence_ = value;
  // @@protoc_insertion_point(field_set:RequestWrapper.sequence)
}

// optional .StartRequest start = 2;
inline bool RequestWrapper::has_start() const {
  return msg_case() == kStart;
}
inline void RequestWrapper::set_has_start() {
  _oneof_case_[0] = kStart;
}
inline void RequestWrapper::clear_start() {
  if (has_start()) {
    delete msg_.start_;
    clear_has_msg();
  }
}
inline  const ::StartRequest& RequestWrapper::start() const {
  // @@protoc_insertion_point(field_get:RequestWrapper.start)
  return has_start()
      ? *msg_.start_
      : ::StartRequest::default_instance();
}
inline ::StartRequest* RequestWrapper::mutable_start() {
  if (!has_start()) {
    clear_msg();
    set_has_start();
    msg_.start_ = new ::StartRequest;
  }
  // @@protoc_insertion_point(field_mutable:RequestWrapper.start)
  return msg_.start_;
}
inline ::StartRequest* RequestWrapper::release_start() {
  // @@protoc_insertion_point(field_release:RequestWrapper.start)
  if (has_start()) {
    clear_has_msg();
    ::StartRequest* temp = msg_.start_;
    msg_.start_ = NULL;
    return temp;
  } else {
    return NULL;
  }
}
inline void RequestWrapper::set_allocated_start(::StartRequest* start) {
  clear_msg();
  if (start) {
    set_has_start();
    msg_.start_ = start;
  }
  // @@protoc_insertion_point(field_set_allocated:RequestWrapper.start)
}

// optional .StopRequest stop = 3;
inline bool RequestWrapper::has_stop() const {
  return msg_case() == kStop;
}
inline void RequestWrapper::set_has_stop() {
  _oneof_case_[0] = kStop;
}
inline void RequestWrapper::clear_stop() {
  if (has_stop()) {
    delete msg_.stop_;
    clear_has_msg();
  }
}
inline  const ::StopRequest& RequestWrapper::stop() const {
  // @@protoc_insertion_point(field_get:RequestWrapper.stop)
  return has_stop()
      ? *msg_.stop_
      : ::StopRequest::default_instance();
}
inline ::StopRequest* RequestWrapper::mutable_stop() {
  if (!has_stop()) {
    clear_msg();
    set_has_stop();
    msg_.stop_ = new ::StopRequest;
  }
  // @@protoc_insertion_point(field_mutable:RequestWrapper.stop)
  return msg_.stop_;
}
inline ::StopRequest* RequestWrapper::release_stop() {
  // @@protoc_insertion_point(field_release:RequestWrapper.stop)
  if (has_stop()) {
    clear_has_msg();
    ::StopRequest* temp = msg_.stop_;
    msg_.stop_ = NULL;
    return temp;
  } else {
    return NULL;
  }
}
inline void RequestWrapper::set_allocated_stop(::StopRequest* stop) {
  clear_msg();
  if (stop) {
    set_has_stop();
    msg_.stop_ = stop;
  }
  // @@protoc_insertion_point(field_set_allocated:RequestWrapper.stop)
}

// optional .SampleRateRequest rate = 4;
inline bool RequestWrapper::has_rate() const {
  return msg_case() == kRate;
}
inline void RequestWrapper::set_has_rate() {
  _oneof_case_[0] = kRate;
}
inline void RequestWrapper::clear_rate() {
  if (has_rate()) {
    delete msg_.rate_;
    clear_has_msg();
  }
}
inline  const ::SampleRateRequest& RequestWrapper::rate() const {
  // @@protoc_insertion_point(field_get:RequestWrapper.rate)
  return has_rate()
      ? *msg_.rate_
      : ::SampleRateRequest::default_instance();
}
inline ::SampleRateRequest* RequestWrapper::mutable_rate() {
  if (!has_rate()) {
    clear_msg();
    set_has_rate();
    msg_.rate_ = new ::SampleRateRequest;
  }
  // @@protoc_insertion_point(field_mutable:RequestWrapper.rate)
  return msg_.rate_;
}
inline ::SampleRateRequest* RequestWrapper::release_rate() {
  // @@protoc_insertion_point(field_release:RequestWrapper.rate)
  if (has_rate()) {
    clear_has_msg();
    ::SampleRateRequest* temp = msg_.rate_;
    msg_.rate_ = NULL;
    return temp;
  } else {
    return NULL;
  }
}
inline void RequestWrapper::set_allocated_rate(::SampleRateRequest* rate) {
  clear_msg();
  if (rate) {
    set_has_rate();
    msg_.rate_ = rate;
  }
  // @@protoc_insertion_point(field_set_allocated:RequestWrapper.rate)
}

// optional .SensitivityRequest sens = 5;
inline bool RequestWrapper::has_sens() const {
  return msg_case() == kSens;
}
inline void RequestWrapper::set_has_sens() {
  _oneof_case_[0] = kSens;
}
inline void RequestWrapper::clear_sens() {
  if (has_sens()) {
    delete msg_.sens_;
    clear_has_msg();
  }
}
inline  const ::SensitivityRequest& RequestWrapper::sens() const {
  // @@protoc_insertion_point(field_get:RequestWrapper.sens)
  return has_sens()
      ? *msg_.sens_
      : ::SensitivityRequest::default_instance();
}
inline ::SensitivityRequest* RequestWrapper::mutable_sens() {
  if (!has_sens()) {
    clear_msg();
    set_has_sens();
    msg_.sens_ = new ::SensitivityRequest;
  }
  // @@protoc_insertion_point(field_mutable:RequestWrapper.sens)
  return msg_.sens_;
}
inline ::SensitivityRequest* RequestWrapper::release_sens() {
  // @@protoc_insertion_point(field_release:RequestWrapper.sens)
  if (has_sens()) {
    clear_has_msg();
    ::SensitivityRequest* temp = msg_.sens_;
    msg_.sens_ = NULL;
    return temp;
  } else {
    return NULL;
  }
}
inline void RequestWrapper::set_allocated_sens(::SensitivityRequest* sens) {
  clear_msg();
  if (sens) {
    set_has_sens();
    msg_.sens_ = sens;
  }
  // @@protoc_insertion_point(field_set_allocated:RequestWrapper.sens)
}

inline bool RequestWrapper::has_msg() const {
  return msg_case() != MSG_NOT_SET;
}
inline void RequestWrapper::clear_has_msg() {
  _oneof_case_[0] = MSG_NOT_SET;
}
inline RequestWrapper::MsgCase RequestWrapper::msg_case() const {
  return RequestWrapper::MsgCase(_oneof_case_[0]);
}
inline const RequestWrapper* RequestWrapper::internal_default_instance() {
  return &RequestWrapper_default_instance_.get();
}
#endif  // !PROTOBUF_INLINE_NOT_IN_HEADERS
// -------------------------------------------------------------------

// -------------------------------------------------------------------

// -------------------------------------------------------------------

// -------------------------------------------------------------------


// @@protoc_insertion_point(namespace_scope)

#ifndef SWIG
namespace google {
namespace protobuf {

template <> struct is_proto_enum< ::SensitivityRequest_Voltage> : ::google::protobuf::internal::true_type {};
template <>
inline const EnumDescriptor* GetEnumDescriptor< ::SensitivityRequest_Voltage>() {
  return ::SensitivityRequest_Voltage_descriptor();
}

}  // namespace protobuf
}  // namespace google
#endif  // SWIG

// @@protoc_insertion_point(global_scope)

#endif  // PROTOBUF_control_5fsignals_2eproto__INCLUDED
