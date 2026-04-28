use crate::config::VoipConfig;
use serde_json::json;

pub trait CallBackend {
    fn start(&mut self, config: &VoipConfig) -> Result<(), String>;
    fn stop(&mut self);
    fn iterate(&mut self) -> Result<Vec<BackendEvent>, String>;
    fn make_call(&mut self, sip_address: &str) -> Result<String, String>;
    fn answer_call(&mut self) -> Result<(), String>;
    fn reject_call(&mut self) -> Result<(), String>;
    fn hangup(&mut self) -> Result<(), String>;
    fn set_muted(&mut self, muted: bool) -> Result<(), String>;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BackendEvent {
    RegistrationChanged { state: String, reason: String },
    IncomingCall { call_id: String, from_uri: String },
    CallStateChanged { call_id: String, state: String },
    BackendStopped { reason: String },
}

#[derive(Debug, Default)]
pub struct VoipHost {
    config: Option<VoipConfig>,
    registered: bool,
    active_call_id: Option<String>,
}

impl VoipHost {
    pub fn configure(&mut self, config: VoipConfig) {
        self.config = Some(config);
        self.registered = false;
        self.active_call_id = None;
    }

    pub fn mark_registered(&mut self, registered: bool) {
        self.registered = registered;
    }

    pub fn set_active_call_id(&mut self, call_id: Option<String>) {
        self.active_call_id = call_id;
    }

    pub fn health_payload(&self) -> serde_json::Value {
        json!({
            "configured": self.config.is_some(),
            "registered": self.registered,
            "active_call_id": self.active_call_id,
        })
    }

    pub fn iterate_interval_ms(&self) -> u64 {
        self.config
            .as_ref()
            .map(|config| config.iterate_interval_ms.max(1))
            .unwrap_or(20)
    }

    pub fn register<B: CallBackend>(&mut self, backend: &mut B) -> Result<(), String> {
        let config = self
            .config
            .as_ref()
            .ok_or_else(|| "voip host is not configured".to_string())?;
        backend.start(config)?;
        self.registered = true;
        Ok(())
    }

    pub fn unregister<B: CallBackend>(&mut self, backend: &mut B) {
        backend.stop();
        self.registered = false;
        self.active_call_id = None;
    }

    pub fn dial<B: CallBackend>(
        &mut self,
        backend: &mut B,
        sip_address: &str,
    ) -> Result<(), String> {
        let call_id = backend.make_call(sip_address)?;
        self.active_call_id = Some(call_id);
        Ok(())
    }

    pub fn answer<B: CallBackend>(&mut self, backend: &mut B) -> Result<(), String> {
        backend.answer_call()
    }

    pub fn reject<B: CallBackend>(&mut self, backend: &mut B) -> Result<(), String> {
        backend.reject_call()?;
        self.active_call_id = None;
        Ok(())
    }

    pub fn hangup<B: CallBackend>(&mut self, backend: &mut B) -> Result<(), String> {
        backend.hangup()?;
        self.active_call_id = None;
        Ok(())
    }

    pub fn set_muted<B: CallBackend>(
        &mut self,
        backend: &mut B,
        muted: bool,
    ) -> Result<(), String> {
        backend.set_muted(muted)
    }

    pub fn poll_backend_events<B: CallBackend>(
        &mut self,
        backend: &mut B,
    ) -> Result<Vec<BackendEvent>, String> {
        let events = backend.iterate()?;
        for event in &events {
            self.apply_backend_event(event);
        }
        Ok(events)
    }

    fn apply_backend_event(&mut self, event: &BackendEvent) {
        match event {
            BackendEvent::RegistrationChanged { state, .. } => {
                if state == "ok" {
                    self.registered = true;
                } else if matches!(state.as_str(), "failed" | "cleared" | "none") {
                    self.registered = false;
                }
            }
            BackendEvent::IncomingCall { call_id, .. } => {
                self.active_call_id = Some(call_id.clone());
            }
            BackendEvent::CallStateChanged { call_id, state } => {
                if matches!(state.as_str(), "idle" | "released" | "error" | "end") {
                    if self.active_call_id.as_deref() == Some(call_id.as_str())
                        || self.active_call_id.is_none()
                    {
                        self.active_call_id = None;
                    }
                } else {
                    self.active_call_id = Some(call_id.clone());
                }
            }
            BackendEvent::BackendStopped { .. } => {
                self.registered = false;
                self.active_call_id = None;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn config() -> VoipConfig {
        VoipConfig::from_payload(&json!({
            "sip_server": "sip.example.com",
            "sip_identity": "sip:alice@example.com"
        }))
        .unwrap()
    }

    #[test]
    fn health_reports_configured_registered_and_call_id() {
        let mut host = VoipHost::default();
        host.configure(config());
        host.mark_registered(true);
        host.set_active_call_id(Some("call-1".to_string()));

        let payload = host.health_payload();

        assert_eq!(payload["configured"], true);
        assert_eq!(payload["registered"], true);
        assert_eq!(payload["active_call_id"], "call-1");
    }
}

#[cfg(test)]
mod command_tests {
    use super::*;
    use serde_json::json;

    #[derive(Default)]
    struct FakeBackend {
        calls: Vec<String>,
    }

    impl CallBackend for FakeBackend {
        fn start(&mut self, _config: &VoipConfig) -> Result<(), String> {
            self.calls.push("start".to_string());
            Ok(())
        }

        fn stop(&mut self) {
            self.calls.push("stop".to_string());
        }

        fn iterate(&mut self) -> Result<Vec<BackendEvent>, String> {
            Ok(vec![])
        }

        fn make_call(&mut self, sip_address: &str) -> Result<String, String> {
            self.calls.push(format!("dial:{sip_address}"));
            Ok("call-outgoing".to_string())
        }

        fn answer_call(&mut self) -> Result<(), String> {
            self.calls.push("answer".to_string());
            Ok(())
        }

        fn reject_call(&mut self) -> Result<(), String> {
            self.calls.push("reject".to_string());
            Ok(())
        }

        fn hangup(&mut self) -> Result<(), String> {
            self.calls.push("hangup".to_string());
            Ok(())
        }

        fn set_muted(&mut self, muted: bool) -> Result<(), String> {
            self.calls.push(format!("mute:{muted}"));
            Ok(())
        }
    }

    fn config() -> VoipConfig {
        VoipConfig::from_payload(&json!({
            "sip_server":"sip.example.com",
            "sip_identity":"sip:alice@example.com"
        }))
        .unwrap()
    }

    #[test]
    fn register_starts_backend_and_health_reports_registered() {
        let mut host = VoipHost::default();
        let mut backend = FakeBackend::default();
        host.configure(config());

        host.register(&mut backend).expect("register");

        assert_eq!(backend.calls, vec!["start"]);
        assert_eq!(host.health_payload()["registered"], true);
    }

    #[test]
    fn dial_sets_active_call_id() {
        let mut host = VoipHost::default();
        let mut backend = FakeBackend::default();
        host.configure(config());
        host.register(&mut backend).unwrap();

        host.dial(&mut backend, "sip:bob@example.com")
            .expect("dial");

        assert_eq!(host.health_payload()["active_call_id"], "call-outgoing");
    }

    #[test]
    fn call_commands_forward_to_backend_and_clear_finished_call() {
        let mut host = VoipHost::default();
        let mut backend = FakeBackend::default();
        host.configure(config());
        host.register(&mut backend).unwrap();
        host.dial(&mut backend, "sip:bob@example.com").unwrap();

        host.answer(&mut backend).expect("answer");
        host.set_muted(&mut backend, true).expect("mute");
        host.hangup(&mut backend).expect("hangup");

        assert_eq!(
            backend.calls,
            vec![
                "start",
                "dial:sip:bob@example.com",
                "answer",
                "mute:true",
                "hangup"
            ]
        );
        assert_eq!(
            host.health_payload()["active_call_id"],
            serde_json::Value::Null
        );
    }

    #[test]
    fn reject_and_unregister_clear_state() {
        let mut host = VoipHost::default();
        let mut backend = FakeBackend::default();
        host.configure(config());
        host.register(&mut backend).unwrap();
        host.dial(&mut backend, "sip:bob@example.com").unwrap();

        host.reject(&mut backend).expect("reject");
        host.unregister(&mut backend);

        assert_eq!(
            backend.calls,
            vec!["start", "dial:sip:bob@example.com", "reject", "stop"]
        );
        assert_eq!(host.health_payload()["registered"], false);
        assert_eq!(
            host.health_payload()["active_call_id"],
            serde_json::Value::Null
        );
    }

    #[test]
    fn poll_backend_events_updates_registration_and_call_state() {
        struct EventBackend {
            events: Vec<BackendEvent>,
        }

        impl CallBackend for EventBackend {
            fn start(&mut self, _config: &VoipConfig) -> Result<(), String> {
                Ok(())
            }

            fn stop(&mut self) {}

            fn iterate(&mut self) -> Result<Vec<BackendEvent>, String> {
                Ok(std::mem::take(&mut self.events))
            }

            fn make_call(&mut self, _sip_address: &str) -> Result<String, String> {
                Ok("call-outgoing".to_string())
            }

            fn answer_call(&mut self) -> Result<(), String> {
                Ok(())
            }

            fn reject_call(&mut self) -> Result<(), String> {
                Ok(())
            }

            fn hangup(&mut self) -> Result<(), String> {
                Ok(())
            }

            fn set_muted(&mut self, _muted: bool) -> Result<(), String> {
                Ok(())
            }
        }

        let mut host = VoipHost::default();
        host.configure(config());
        let mut backend = EventBackend {
            events: vec![
                BackendEvent::RegistrationChanged {
                    state: "ok".to_string(),
                    reason: "".to_string(),
                },
                BackendEvent::IncomingCall {
                    call_id: "call-1".to_string(),
                    from_uri: "sip:bob@example.com".to_string(),
                },
                BackendEvent::CallStateChanged {
                    call_id: "call-1".to_string(),
                    state: "released".to_string(),
                },
            ],
        };

        let events = host.poll_backend_events(&mut backend).expect("poll");

        assert_eq!(events.len(), 3);
        assert_eq!(host.health_payload()["registered"], true);
        assert_eq!(
            host.health_payload()["active_call_id"],
            serde_json::Value::Null
        );
    }

    #[test]
    fn iterate_interval_comes_from_config() {
        let mut host = VoipHost::default();
        host.configure(
            VoipConfig::from_payload(&json!({
                "sip_server":"sip.example.com",
                "sip_identity":"sip:alice@example.com",
                "iterate_interval_ms": 37
            }))
            .unwrap(),
        );

        assert_eq!(host.iterate_interval_ms(), 37);
    }
}
