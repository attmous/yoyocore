use std::ffi::CStr;
use std::os::raw::{c_char, c_float, c_int, c_void};
use std::sync::Arc;

#[repr(C)]
pub struct LinphoneFactory {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneCore {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneCoreCbs {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneAccount {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneAccountCbs {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneAccountParams {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneAuthInfo {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneAddress {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneCall {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneCallParams {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneChatRoom {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneChatRoomCbs {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneChatMessage {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneChatMessageCbs {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneContent {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneEventLog {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneImNotifPolicy {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneNatPolicy {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneRecorder {
    _private: [u8; 0],
}
#[repr(C)]
pub struct LinphoneRecorderParams {
    _private: [u8; 0],
}

pub type CoreCallStateChangedCb =
    Option<unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneCall, c_int, *const c_char)>;
pub type CoreMessageReceivedCb = Option<
    unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneChatRoom, *mut LinphoneChatMessage),
>;
pub type CoreMessageUnableDecryptCb = Option<
    unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneChatRoom, *mut LinphoneChatMessage),
>;
pub type AccountRegistrationChangedCb =
    Option<unsafe extern "C" fn(*mut LinphoneAccount, c_int, *const c_char)>;
pub type ChatMessageStateChangedCb = Option<unsafe extern "C" fn(*mut LinphoneChatMessage, c_int)>;
pub type ChatRoomMessageReceivedCb =
    Option<unsafe extern "C" fn(*mut LinphoneChatRoom, *mut LinphoneChatMessage)>;
pub type ChatRoomMessagesReceivedCb =
    Option<unsafe extern "C" fn(*mut LinphoneChatRoom, *const c_void)>;
pub type ChatRoomEventLogReceivedCb =
    Option<unsafe extern "C" fn(*mut LinphoneChatRoom, *mut LinphoneEventLog)>;

unsafe extern "C" {
    #[cfg(unix)]
    fn dlsym(handle: *mut c_void, symbol: *const c_char) -> *mut c_void;

    fn linphone_factory_get() -> *mut LinphoneFactory;
    fn linphone_factory_create_core_3(
        factory: *mut LinphoneFactory,
        config_path: *const c_char,
        factory_config_path: *const c_char,
        userdata: *mut c_void,
    ) -> *mut LinphoneCore;
    fn linphone_factory_create_core_cbs(factory: *mut LinphoneFactory) -> *mut LinphoneCoreCbs;
    fn linphone_factory_create_chat_room_cbs(
        factory: *mut LinphoneFactory,
    ) -> *mut LinphoneChatRoomCbs;
    fn linphone_factory_create_address(
        factory: *mut LinphoneFactory,
        address: *const c_char,
    ) -> *mut LinphoneAddress;
    fn linphone_factory_create_auth_info_2(
        factory: *mut LinphoneFactory,
        username: *const c_char,
        userid: *const c_char,
        passwd: *const c_char,
        ha1: *const c_char,
        realm: *const c_char,
        domain: *const c_char,
        algorithm: *const c_char,
    ) -> *mut LinphoneAuthInfo;
    fn linphone_core_cbs_set_call_state_changed(
        cbs: *mut LinphoneCoreCbs,
        callback: CoreCallStateChangedCb,
    );
    fn linphone_core_cbs_set_message_received(
        cbs: *mut LinphoneCoreCbs,
        callback: CoreMessageReceivedCb,
    );
    fn linphone_core_add_callbacks(core: *mut LinphoneCore, cbs: *mut LinphoneCoreCbs);
    fn linphone_core_start(core: *mut LinphoneCore) -> c_int;
    fn linphone_core_stop(core: *mut LinphoneCore);
    fn linphone_core_unref(core: *mut LinphoneCore);
    fn linphone_core_iterate(core: *mut LinphoneCore);
    fn linphone_core_enable_chat(core: *mut LinphoneCore);
    fn linphone_core_set_playback_device(core: *mut LinphoneCore, device: *const c_char);
    fn linphone_core_set_ringer_device(core: *mut LinphoneCore, device: *const c_char);
    fn linphone_core_set_capture_device(core: *mut LinphoneCore, device: *const c_char);
    fn linphone_core_set_media_device(core: *mut LinphoneCore, device: *const c_char);
    fn linphone_core_enable_echo_cancellation(core: *mut LinphoneCore, enabled: c_int);
    fn linphone_core_set_mic_gain_db(core: *mut LinphoneCore, gain: c_float);
    fn linphone_core_set_playback_gain_db(core: *mut LinphoneCore, gain: c_float);
    fn linphone_core_set_audio_port_range(
        core: *mut LinphoneCore,
        min_port: c_int,
        max_port: c_int,
    );
    fn linphone_core_set_video_port_range(
        core: *mut LinphoneCore,
        min_port: c_int,
        max_port: c_int,
    );
    fn linphone_core_create_nat_policy(core: *mut LinphoneCore) -> *mut LinphoneNatPolicy;
    fn linphone_core_set_nat_policy(core: *mut LinphoneCore, policy: *mut LinphoneNatPolicy);
    fn linphone_core_set_stun_server(core: *mut LinphoneCore, server: *const c_char);
    fn linphone_core_set_file_transfer_server(core: *mut LinphoneCore, server: *const c_char);
    fn linphone_core_create_account_params(core: *mut LinphoneCore) -> *mut LinphoneAccountParams;
    fn linphone_core_create_account(
        core: *mut LinphoneCore,
        params: *mut LinphoneAccountParams,
    ) -> *mut LinphoneAccount;
    fn linphone_core_add_account(core: *mut LinphoneCore, account: *mut LinphoneAccount) -> c_int;
    fn linphone_core_set_default_account(core: *mut LinphoneCore, account: *mut LinphoneAccount);
    fn linphone_core_add_auth_info(core: *mut LinphoneCore, auth_info: *mut LinphoneAuthInfo);
    fn linphone_core_create_call_params(
        core: *mut LinphoneCore,
        call: *mut LinphoneCall,
    ) -> *mut LinphoneCallParams;
    fn linphone_core_invite_address_with_params(
        core: *mut LinphoneCore,
        address: *mut LinphoneAddress,
        params: *mut LinphoneCallParams,
    ) -> *mut LinphoneCall;
    fn linphone_core_get_chat_room_from_uri(
        core: *mut LinphoneCore,
        uri: *const c_char,
    ) -> *mut LinphoneChatRoom;
    fn linphone_account_params_set_server_address(
        params: *mut LinphoneAccountParams,
        address: *mut LinphoneAddress,
    ) -> c_int;
    fn linphone_account_params_set_identity_address(
        params: *mut LinphoneAccountParams,
        address: *mut LinphoneAddress,
    ) -> c_int;
    fn linphone_account_params_enable_register(params: *mut LinphoneAccountParams, enabled: c_int);
    fn linphone_account_cbs_new() -> *mut LinphoneAccountCbs;
    fn linphone_account_cbs_set_registration_state_changed(
        cbs: *mut LinphoneAccountCbs,
        callback: AccountRegistrationChangedCb,
    );
    fn linphone_account_add_callbacks(account: *mut LinphoneAccount, cbs: *mut LinphoneAccountCbs);
    fn linphone_account_unref(account: *mut LinphoneAccount);
    fn linphone_account_cbs_unref(cbs: *mut LinphoneAccountCbs);
    fn linphone_account_params_unref(params: *mut LinphoneAccountParams);
    fn linphone_address_get_username(address: *const LinphoneAddress) -> *const c_char;
    fn linphone_address_get_domain(address: *const LinphoneAddress) -> *const c_char;
    fn linphone_address_unref(address: *mut LinphoneAddress);
    fn linphone_auth_info_unref(auth_info: *mut LinphoneAuthInfo);
    fn linphone_call_params_unref(params: *mut LinphoneCallParams);
    fn linphone_call_get_remote_address(call: *mut LinphoneCall) -> *const LinphoneAddress;
    fn linphone_call_accept(call: *mut LinphoneCall) -> c_int;
    fn linphone_call_decline(call: *mut LinphoneCall, reason: c_int) -> c_int;
    fn linphone_call_terminate(call: *mut LinphoneCall) -> c_int;
    fn linphone_call_set_microphone_muted(call: *mut LinphoneCall, muted: c_int);
    fn linphone_chat_room_add_callbacks(
        chat_room: *mut LinphoneChatRoom,
        cbs: *mut LinphoneChatRoomCbs,
    );
    fn linphone_chat_room_create_message_from_utf8(
        chat_room: *mut LinphoneChatRoom,
        text: *const c_char,
    ) -> *mut LinphoneChatMessage;
    fn linphone_chat_room_cbs_set_message_received(
        cbs: *mut LinphoneChatRoomCbs,
        callback: ChatRoomMessageReceivedCb,
    );
    fn linphone_chat_message_cbs_new() -> *mut LinphoneChatMessageCbs;
    fn linphone_chat_message_cbs_unref(cbs: *mut LinphoneChatMessageCbs);
    fn linphone_chat_message_cbs_set_msg_state_changed(
        cbs: *mut LinphoneChatMessageCbs,
        callback: ChatMessageStateChangedCb,
    );
    fn linphone_chat_message_add_callbacks(
        message: *mut LinphoneChatMessage,
        cbs: *mut LinphoneChatMessageCbs,
    );
    fn linphone_chat_message_send(message: *mut LinphoneChatMessage);
    fn linphone_chat_message_get_message_id(message: *mut LinphoneChatMessage) -> *const c_char;
    fn linphone_chat_message_get_user_data(message: *mut LinphoneChatMessage) -> *mut c_void;
    fn linphone_chat_message_set_user_data(message: *mut LinphoneChatMessage, data: *mut c_void);
    fn linphone_chat_message_get_file_transfer_information(
        message: *mut LinphoneChatMessage,
    ) -> *mut LinphoneContent;
    fn linphone_chat_message_get_state(message: *mut LinphoneChatMessage) -> c_int;
    fn linphone_chat_message_state_to_string(state: c_int) -> *const c_char;
    fn linphone_chat_message_is_outgoing(message: *const LinphoneChatMessage) -> c_int;
    fn linphone_chat_message_is_read(message: *mut LinphoneChatMessage) -> c_int;
    fn linphone_chat_message_get_peer_address(
        message: *mut LinphoneChatMessage,
    ) -> *const LinphoneAddress;
    fn linphone_chat_message_get_from_address(
        message: *mut LinphoneChatMessage,
    ) -> *const LinphoneAddress;
    fn linphone_chat_message_get_to_address(
        message: *mut LinphoneChatMessage,
    ) -> *const LinphoneAddress;
    fn linphone_chat_message_download_content(
        message: *mut LinphoneChatMessage,
        content: *mut LinphoneContent,
    );
    fn linphone_content_get_type(content: *const LinphoneContent) -> *const c_char;
    fn linphone_content_get_subtype(content: *const LinphoneContent) -> *const c_char;
    fn linphone_content_get_file_path(content: *const LinphoneContent) -> *const c_char;
    fn linphone_content_set_file_path(content: *mut LinphoneContent, path: *const c_char);
    fn linphone_core_cbs_unref(cbs: *mut LinphoneCoreCbs);
    fn linphone_chat_room_cbs_unref(cbs: *mut LinphoneChatRoomCbs);
    fn linphone_nat_policy_enable_stun(policy: *mut LinphoneNatPolicy, enabled: c_int);
    fn linphone_nat_policy_enable_ice(policy: *mut LinphoneNatPolicy, enabled: c_int);
    fn linphone_nat_policy_set_stun_server(policy: *mut LinphoneNatPolicy, server: *const c_char);
    fn linphone_nat_policy_unref(policy: *mut LinphoneNatPolicy);
    fn linphone_core_get_version() -> *const c_char;
}

pub struct LinphoneApi {
    pub factory_get: unsafe extern "C" fn() -> *mut LinphoneFactory,
    pub factory_create_core_3: unsafe extern "C" fn(
        *mut LinphoneFactory,
        *const c_char,
        *const c_char,
        *mut c_void,
    ) -> *mut LinphoneCore,
    pub factory_create_core_cbs: unsafe extern "C" fn(*mut LinphoneFactory) -> *mut LinphoneCoreCbs,
    pub factory_create_chat_room_cbs:
        unsafe extern "C" fn(*mut LinphoneFactory) -> *mut LinphoneChatRoomCbs,
    pub factory_create_address:
        unsafe extern "C" fn(*mut LinphoneFactory, *const c_char) -> *mut LinphoneAddress,
    pub factory_create_auth_info_2: unsafe extern "C" fn(
        *mut LinphoneFactory,
        *const c_char,
        *const c_char,
        *const c_char,
        *const c_char,
        *const c_char,
        *const c_char,
        *const c_char,
    ) -> *mut LinphoneAuthInfo,
    pub core_cbs_set_call_state_changed:
        unsafe extern "C" fn(*mut LinphoneCoreCbs, CoreCallStateChangedCb),
    pub core_cbs_set_message_received:
        unsafe extern "C" fn(*mut LinphoneCoreCbs, CoreMessageReceivedCb),
    pub core_cbs_set_message_received_unable_decrypt:
        Option<unsafe extern "C" fn(*mut LinphoneCoreCbs, CoreMessageUnableDecryptCb)>,
    pub core_add_callbacks: unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneCoreCbs),
    pub core_start: unsafe extern "C" fn(*mut LinphoneCore) -> c_int,
    pub core_stop: unsafe extern "C" fn(*mut LinphoneCore),
    pub core_unref: unsafe extern "C" fn(*mut LinphoneCore),
    pub core_iterate: unsafe extern "C" fn(*mut LinphoneCore),
    pub core_enable_chat: unsafe extern "C" fn(*mut LinphoneCore),
    pub core_set_playback_device: unsafe extern "C" fn(*mut LinphoneCore, *const c_char),
    pub core_set_ringer_device: unsafe extern "C" fn(*mut LinphoneCore, *const c_char),
    pub core_set_capture_device: unsafe extern "C" fn(*mut LinphoneCore, *const c_char),
    pub core_set_media_device: unsafe extern "C" fn(*mut LinphoneCore, *const c_char),
    pub core_enable_echo_cancellation: unsafe extern "C" fn(*mut LinphoneCore, c_int),
    pub core_set_mic_gain_db: unsafe extern "C" fn(*mut LinphoneCore, c_float),
    pub core_set_playback_gain_db: unsafe extern "C" fn(*mut LinphoneCore, c_float),
    pub core_set_audio_port_range: unsafe extern "C" fn(*mut LinphoneCore, c_int, c_int),
    pub core_set_video_port_range: unsafe extern "C" fn(*mut LinphoneCore, c_int, c_int),
    pub core_create_nat_policy: unsafe extern "C" fn(*mut LinphoneCore) -> *mut LinphoneNatPolicy,
    pub core_set_nat_policy: unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneNatPolicy),
    pub core_set_stun_server: unsafe extern "C" fn(*mut LinphoneCore, *const c_char),
    pub core_set_file_transfer_server: unsafe extern "C" fn(*mut LinphoneCore, *const c_char),
    pub core_enable_lime_x3dh: Option<unsafe extern "C" fn(*mut LinphoneCore, c_int)>,
    pub core_get_im_notif_policy:
        Option<unsafe extern "C" fn(*mut LinphoneCore) -> *mut LinphoneImNotifPolicy>,
    pub core_add_linphone_spec: Option<unsafe extern "C" fn(*mut LinphoneCore, *const c_char)>,
    pub core_set_chat_messages_aggregation_enabled:
        Option<unsafe extern "C" fn(*mut LinphoneCore, c_int)>,
    pub core_enable_auto_download_voice_recordings:
        Option<unsafe extern "C" fn(*mut LinphoneCore, c_int)>,
    pub core_create_account_params:
        unsafe extern "C" fn(*mut LinphoneCore) -> *mut LinphoneAccountParams,
    pub core_create_account:
        unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneAccountParams) -> *mut LinphoneAccount,
    pub core_add_account: unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneAccount) -> c_int,
    pub core_set_default_account: unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneAccount),
    pub core_add_auth_info: unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneAuthInfo),
    pub core_create_call_params:
        unsafe extern "C" fn(*mut LinphoneCore, *mut LinphoneCall) -> *mut LinphoneCallParams,
    pub core_invite_address_with_params: unsafe extern "C" fn(
        *mut LinphoneCore,
        *mut LinphoneAddress,
        *mut LinphoneCallParams,
    ) -> *mut LinphoneCall,
    pub core_get_chat_room_from_uri:
        unsafe extern "C" fn(*mut LinphoneCore, *const c_char) -> *mut LinphoneChatRoom,
    pub core_create_recorder_params:
        Option<unsafe extern "C" fn(*mut LinphoneCore) -> *mut LinphoneRecorderParams>,
    pub core_create_recorder: Option<
        unsafe extern "C" fn(
            *mut LinphoneCore,
            *mut LinphoneRecorderParams,
        ) -> *mut LinphoneRecorder,
    >,
    pub account_params_set_server_address:
        unsafe extern "C" fn(*mut LinphoneAccountParams, *mut LinphoneAddress) -> c_int,
    pub account_params_set_identity_address:
        unsafe extern "C" fn(*mut LinphoneAccountParams, *mut LinphoneAddress) -> c_int,
    pub account_params_enable_register: unsafe extern "C" fn(*mut LinphoneAccountParams, c_int),
    pub account_params_enable_cpim_in_basic_chat_room:
        Option<unsafe extern "C" fn(*mut LinphoneAccountParams, c_int)>,
    pub account_params_set_conference_factory_address:
        Option<unsafe extern "C" fn(*mut LinphoneAccountParams, *mut LinphoneAddress)>,
    pub account_params_set_audio_video_conference_factory_address:
        Option<unsafe extern "C" fn(*mut LinphoneAccountParams, *mut LinphoneAddress)>,
    pub account_params_set_file_transfer_server:
        Option<unsafe extern "C" fn(*mut LinphoneAccountParams, *const c_char)>,
    pub account_params_set_lime_server_url:
        Option<unsafe extern "C" fn(*mut LinphoneAccountParams, *const c_char)>,
    pub account_cbs_new: unsafe extern "C" fn() -> *mut LinphoneAccountCbs,
    pub account_cbs_set_registration_state_changed:
        unsafe extern "C" fn(*mut LinphoneAccountCbs, AccountRegistrationChangedCb),
    pub account_add_callbacks: unsafe extern "C" fn(*mut LinphoneAccount, *mut LinphoneAccountCbs),
    pub account_unref: unsafe extern "C" fn(*mut LinphoneAccount),
    pub account_cbs_unref: unsafe extern "C" fn(*mut LinphoneAccountCbs),
    pub account_params_unref: unsafe extern "C" fn(*mut LinphoneAccountParams),
    pub address_get_username: unsafe extern "C" fn(*const LinphoneAddress) -> *const c_char,
    pub address_get_domain: unsafe extern "C" fn(*const LinphoneAddress) -> *const c_char,
    pub address_unref: unsafe extern "C" fn(*mut LinphoneAddress),
    pub auth_info_unref: unsafe extern "C" fn(*mut LinphoneAuthInfo),
    pub call_params_unref: unsafe extern "C" fn(*mut LinphoneCallParams),
    pub call_get_remote_address: unsafe extern "C" fn(*mut LinphoneCall) -> *const LinphoneAddress,
    pub call_accept: unsafe extern "C" fn(*mut LinphoneCall) -> c_int,
    pub call_decline: unsafe extern "C" fn(*mut LinphoneCall, c_int) -> c_int,
    pub call_terminate: unsafe extern "C" fn(*mut LinphoneCall) -> c_int,
    pub call_set_microphone_muted: unsafe extern "C" fn(*mut LinphoneCall, c_int),
    pub chat_room_add_callbacks:
        unsafe extern "C" fn(*mut LinphoneChatRoom, *mut LinphoneChatRoomCbs),
    pub chat_room_create_message_from_utf8:
        unsafe extern "C" fn(*mut LinphoneChatRoom, *const c_char) -> *mut LinphoneChatMessage,
    pub chat_room_create_voice_recording_message: Option<
        unsafe extern "C" fn(
            *mut LinphoneChatRoom,
            *mut LinphoneRecorder,
        ) -> *mut LinphoneChatMessage,
    >,
    pub chat_room_cbs_set_message_received:
        unsafe extern "C" fn(*mut LinphoneChatRoomCbs, ChatRoomMessageReceivedCb),
    pub chat_room_cbs_set_messages_received:
        Option<unsafe extern "C" fn(*mut LinphoneChatRoomCbs, ChatRoomMessagesReceivedCb)>,
    pub chat_room_cbs_set_chat_message_received:
        Option<unsafe extern "C" fn(*mut LinphoneChatRoomCbs, ChatRoomEventLogReceivedCb)>,
    pub chat_message_cbs_new: unsafe extern "C" fn() -> *mut LinphoneChatMessageCbs,
    pub chat_message_cbs_unref: unsafe extern "C" fn(*mut LinphoneChatMessageCbs),
    pub chat_message_cbs_set_msg_state_changed:
        unsafe extern "C" fn(*mut LinphoneChatMessageCbs, ChatMessageStateChangedCb),
    pub chat_message_add_callbacks:
        unsafe extern "C" fn(*mut LinphoneChatMessage, *mut LinphoneChatMessageCbs),
    pub chat_message_send: unsafe extern "C" fn(*mut LinphoneChatMessage),
    pub chat_message_get_message_id:
        unsafe extern "C" fn(*mut LinphoneChatMessage) -> *const c_char,
    pub chat_message_get_user_data: unsafe extern "C" fn(*mut LinphoneChatMessage) -> *mut c_void,
    pub chat_message_set_user_data: unsafe extern "C" fn(*mut LinphoneChatMessage, *mut c_void),
    pub chat_message_get_utf8_text:
        Option<unsafe extern "C" fn(*const LinphoneChatMessage) -> *const c_char>,
    pub chat_message_get_text:
        Option<unsafe extern "C" fn(*const LinphoneChatMessage) -> *const c_char>,
    pub chat_message_get_file_transfer_information:
        unsafe extern "C" fn(*mut LinphoneChatMessage) -> *mut LinphoneContent,
    pub chat_message_get_state: unsafe extern "C" fn(*mut LinphoneChatMessage) -> c_int,
    pub chat_message_state_to_string: unsafe extern "C" fn(c_int) -> *const c_char,
    pub chat_message_is_outgoing: unsafe extern "C" fn(*const LinphoneChatMessage) -> c_int,
    pub chat_message_is_read: unsafe extern "C" fn(*mut LinphoneChatMessage) -> c_int,
    pub chat_message_get_peer_address:
        unsafe extern "C" fn(*mut LinphoneChatMessage) -> *const LinphoneAddress,
    pub chat_message_get_from_address:
        unsafe extern "C" fn(*mut LinphoneChatMessage) -> *const LinphoneAddress,
    pub chat_message_get_to_address:
        unsafe extern "C" fn(*mut LinphoneChatMessage) -> *const LinphoneAddress,
    pub chat_message_download_content:
        unsafe extern "C" fn(*mut LinphoneChatMessage, *mut LinphoneContent),
    pub content_get_type: unsafe extern "C" fn(*const LinphoneContent) -> *const c_char,
    pub content_get_subtype: unsafe extern "C" fn(*const LinphoneContent) -> *const c_char,
    pub content_get_file_path: unsafe extern "C" fn(*const LinphoneContent) -> *const c_char,
    pub content_set_file_path: unsafe extern "C" fn(*mut LinphoneContent, *const c_char),
    pub core_cbs_unref: unsafe extern "C" fn(*mut LinphoneCoreCbs),
    pub chat_room_cbs_unref: unsafe extern "C" fn(*mut LinphoneChatRoomCbs),
    pub event_log_get_chat_message:
        Option<unsafe extern "C" fn(*mut LinphoneEventLog) -> *mut LinphoneChatMessage>,
    pub im_notif_policy_enable_all: Option<unsafe extern "C" fn(*mut LinphoneImNotifPolicy)>,
    pub nat_policy_enable_stun: unsafe extern "C" fn(*mut LinphoneNatPolicy, c_int),
    pub nat_policy_enable_ice: unsafe extern "C" fn(*mut LinphoneNatPolicy, c_int),
    pub nat_policy_set_stun_server: unsafe extern "C" fn(*mut LinphoneNatPolicy, *const c_char),
    pub nat_policy_unref: unsafe extern "C" fn(*mut LinphoneNatPolicy),
    pub recorder_params_set_file_format:
        Option<unsafe extern "C" fn(*mut LinphoneRecorderParams, c_int)>,
    pub recorder_params_unref: Option<unsafe extern "C" fn(*mut LinphoneRecorderParams)>,
    pub recorder_open: Option<unsafe extern "C" fn(*mut LinphoneRecorder, *const c_char) -> c_int>,
    pub recorder_start: Option<unsafe extern "C" fn(*mut LinphoneRecorder) -> c_int>,
    pub recorder_pause: Option<unsafe extern "C" fn(*mut LinphoneRecorder) -> c_int>,
    pub recorder_get_duration: Option<unsafe extern "C" fn(*mut LinphoneRecorder) -> c_int>,
    pub recorder_close: Option<unsafe extern "C" fn(*mut LinphoneRecorder) -> c_int>,
    pub recorder_unref: Option<unsafe extern "C" fn(*mut LinphoneRecorder)>,
    pub core_get_version: unsafe extern "C" fn() -> *const c_char,
    pub registration_state_to_string: Option<unsafe extern "C" fn(c_int) -> *const c_char>,
    pub call_state_to_string: Option<unsafe extern "C" fn(c_int) -> *const c_char>,
}

impl LinphoneApi {
    pub unsafe fn load() -> Result<Arc<Self>, String> {
        Ok(Arc::new(Self {
            factory_get: linphone_factory_get,
            factory_create_core_3: linphone_factory_create_core_3,
            factory_create_core_cbs: linphone_factory_create_core_cbs,
            factory_create_chat_room_cbs: linphone_factory_create_chat_room_cbs,
            factory_create_address: linphone_factory_create_address,
            factory_create_auth_info_2: linphone_factory_create_auth_info_2,
            core_cbs_set_call_state_changed: linphone_core_cbs_set_call_state_changed,
            core_cbs_set_message_received: linphone_core_cbs_set_message_received,
            core_cbs_set_message_received_unable_decrypt: unsafe {
                optional_symbol(c"linphone_core_cbs_set_message_received_unable_decrypt")
            },
            core_add_callbacks: linphone_core_add_callbacks,
            core_start: linphone_core_start,
            core_stop: linphone_core_stop,
            core_unref: linphone_core_unref,
            core_iterate: linphone_core_iterate,
            core_enable_chat: linphone_core_enable_chat,
            core_set_playback_device: linphone_core_set_playback_device,
            core_set_ringer_device: linphone_core_set_ringer_device,
            core_set_capture_device: linphone_core_set_capture_device,
            core_set_media_device: linphone_core_set_media_device,
            core_enable_echo_cancellation: linphone_core_enable_echo_cancellation,
            core_set_mic_gain_db: linphone_core_set_mic_gain_db,
            core_set_playback_gain_db: linphone_core_set_playback_gain_db,
            core_set_audio_port_range: linphone_core_set_audio_port_range,
            core_set_video_port_range: linphone_core_set_video_port_range,
            core_create_nat_policy: linphone_core_create_nat_policy,
            core_set_nat_policy: linphone_core_set_nat_policy,
            core_set_stun_server: linphone_core_set_stun_server,
            core_set_file_transfer_server: linphone_core_set_file_transfer_server,
            core_enable_lime_x3dh: unsafe { optional_symbol(c"linphone_core_enable_lime_x3dh") },
            core_get_im_notif_policy: unsafe {
                optional_symbol(c"linphone_core_get_im_notif_policy")
            },
            core_add_linphone_spec: unsafe { optional_symbol(c"linphone_core_add_linphone_spec") },
            core_set_chat_messages_aggregation_enabled: unsafe {
                optional_symbol(c"linphone_core_set_chat_messages_aggregation_enabled")
            },
            core_enable_auto_download_voice_recordings: unsafe {
                optional_symbol(c"linphone_core_enable_auto_download_voice_recordings")
            },
            core_create_account_params: linphone_core_create_account_params,
            core_create_account: linphone_core_create_account,
            core_add_account: linphone_core_add_account,
            core_set_default_account: linphone_core_set_default_account,
            core_add_auth_info: linphone_core_add_auth_info,
            core_create_call_params: linphone_core_create_call_params,
            core_invite_address_with_params: linphone_core_invite_address_with_params,
            core_get_chat_room_from_uri: linphone_core_get_chat_room_from_uri,
            core_create_recorder_params: unsafe {
                optional_symbol(c"linphone_core_create_recorder_params")
            },
            core_create_recorder: unsafe { optional_symbol(c"linphone_core_create_recorder") },
            account_params_set_server_address: linphone_account_params_set_server_address,
            account_params_set_identity_address: linphone_account_params_set_identity_address,
            account_params_enable_register: linphone_account_params_enable_register,
            account_params_enable_cpim_in_basic_chat_room: unsafe {
                optional_symbol(c"linphone_account_params_enable_cpim_in_basic_chat_room")
            },
            account_params_set_conference_factory_address: unsafe {
                optional_symbol(c"linphone_account_params_set_conference_factory_address")
            },
            account_params_set_audio_video_conference_factory_address: unsafe {
                optional_symbol(
                    c"linphone_account_params_set_audio_video_conference_factory_address",
                )
            },
            account_params_set_file_transfer_server: unsafe {
                optional_symbol(c"linphone_account_params_set_file_transfer_server")
            },
            account_params_set_lime_server_url: unsafe {
                optional_symbol(c"linphone_account_params_set_lime_server_url")
            },
            account_cbs_new: linphone_account_cbs_new,
            account_cbs_set_registration_state_changed:
                linphone_account_cbs_set_registration_state_changed,
            account_add_callbacks: linphone_account_add_callbacks,
            account_unref: linphone_account_unref,
            account_cbs_unref: linphone_account_cbs_unref,
            account_params_unref: linphone_account_params_unref,
            address_get_username: linphone_address_get_username,
            address_get_domain: linphone_address_get_domain,
            address_unref: linphone_address_unref,
            auth_info_unref: linphone_auth_info_unref,
            call_params_unref: linphone_call_params_unref,
            call_get_remote_address: linphone_call_get_remote_address,
            call_accept: linphone_call_accept,
            call_decline: linphone_call_decline,
            call_terminate: linphone_call_terminate,
            call_set_microphone_muted: linphone_call_set_microphone_muted,
            chat_room_add_callbacks: linphone_chat_room_add_callbacks,
            chat_room_create_message_from_utf8: linphone_chat_room_create_message_from_utf8,
            chat_room_create_voice_recording_message: unsafe {
                optional_symbol(c"linphone_chat_room_create_voice_recording_message")
            },
            chat_room_cbs_set_message_received: linphone_chat_room_cbs_set_message_received,
            chat_room_cbs_set_messages_received: unsafe {
                optional_symbol(c"linphone_chat_room_cbs_set_messages_received")
            },
            chat_room_cbs_set_chat_message_received: unsafe {
                optional_symbol(c"linphone_chat_room_cbs_set_chat_message_received")
            },
            chat_message_cbs_new: linphone_chat_message_cbs_new,
            chat_message_cbs_unref: linphone_chat_message_cbs_unref,
            chat_message_cbs_set_msg_state_changed: linphone_chat_message_cbs_set_msg_state_changed,
            chat_message_add_callbacks: linphone_chat_message_add_callbacks,
            chat_message_send: linphone_chat_message_send,
            chat_message_get_message_id: linphone_chat_message_get_message_id,
            chat_message_get_user_data: linphone_chat_message_get_user_data,
            chat_message_set_user_data: linphone_chat_message_set_user_data,
            chat_message_get_utf8_text: unsafe {
                optional_symbol(c"linphone_chat_message_get_utf8_text")
            },
            chat_message_get_text: unsafe { optional_symbol(c"linphone_chat_message_get_text") },
            chat_message_get_file_transfer_information:
                linphone_chat_message_get_file_transfer_information,
            chat_message_get_state: linphone_chat_message_get_state,
            chat_message_state_to_string: linphone_chat_message_state_to_string,
            chat_message_is_outgoing: linphone_chat_message_is_outgoing,
            chat_message_is_read: linphone_chat_message_is_read,
            chat_message_get_peer_address: linphone_chat_message_get_peer_address,
            chat_message_get_from_address: linphone_chat_message_get_from_address,
            chat_message_get_to_address: linphone_chat_message_get_to_address,
            chat_message_download_content: linphone_chat_message_download_content,
            content_get_type: linphone_content_get_type,
            content_get_subtype: linphone_content_get_subtype,
            content_get_file_path: linphone_content_get_file_path,
            content_set_file_path: linphone_content_set_file_path,
            core_cbs_unref: linphone_core_cbs_unref,
            chat_room_cbs_unref: linphone_chat_room_cbs_unref,
            event_log_get_chat_message: unsafe {
                optional_symbol(c"linphone_event_log_get_chat_message")
            },
            im_notif_policy_enable_all: unsafe {
                optional_symbol(c"linphone_im_notif_policy_enable_all")
            },
            nat_policy_enable_stun: linphone_nat_policy_enable_stun,
            nat_policy_enable_ice: linphone_nat_policy_enable_ice,
            nat_policy_set_stun_server: linphone_nat_policy_set_stun_server,
            nat_policy_unref: linphone_nat_policy_unref,
            recorder_params_set_file_format: unsafe {
                optional_symbol(c"linphone_recorder_params_set_file_format")
            },
            recorder_params_unref: unsafe { optional_symbol(c"linphone_recorder_params_unref") },
            recorder_open: unsafe { optional_symbol(c"linphone_recorder_open") },
            recorder_start: unsafe { optional_symbol(c"linphone_recorder_start") },
            recorder_pause: unsafe { optional_symbol(c"linphone_recorder_pause") },
            recorder_get_duration: unsafe { optional_symbol(c"linphone_recorder_get_duration") },
            recorder_close: unsafe { optional_symbol(c"linphone_recorder_close") },
            recorder_unref: unsafe { optional_symbol(c"linphone_recorder_unref") },
            core_get_version: linphone_core_get_version,
            registration_state_to_string: unsafe {
                optional_symbol(c"linphone_registration_state_to_string")
            },
            call_state_to_string: unsafe { optional_symbol(c"linphone_call_state_to_string") },
        }))
    }
}

#[cfg(unix)]
unsafe fn optional_symbol<T: Copy>(name: &CStr) -> Option<T> {
    let symbol = unsafe { dlsym(std::ptr::null_mut(), name.as_ptr()) };
    if symbol.is_null() {
        return None;
    }
    debug_assert_eq!(std::mem::size_of::<T>(), std::mem::size_of::<*mut c_void>());
    Some(unsafe { std::mem::transmute_copy::<*mut c_void, T>(&symbol) })
}

#[cfg(not(unix))]
unsafe fn optional_symbol<T>(_name: &CStr) -> Option<T> {
    None
}
