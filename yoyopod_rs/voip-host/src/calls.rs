#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CallSession {
    state: String,
    active_call_id: Option<String>,
    active_peer: String,
    muted: bool,
}

impl Default for CallSession {
    fn default() -> Self {
        Self {
            state: "idle".to_string(),
            active_call_id: None,
            active_peer: String::new(),
            muted: false,
        }
    }
}

impl CallSession {
    pub fn state(&self) -> &str {
        &self.state
    }

    pub fn active_call_id(&self) -> Option<&str> {
        self.active_call_id.as_deref()
    }

    pub fn active_peer(&self) -> &str {
        &self.active_peer
    }

    pub fn muted(&self) -> bool {
        self.muted
    }

    pub fn set_active_call_id(&mut self, call_id: Option<String>) {
        self.active_call_id = call_id;
    }

    pub fn start_outgoing(&mut self, call_id: &str, peer: &str) {
        self.active_call_id = Some(call_id.to_string());
        self.active_peer = peer.to_string();
        self.state = "outgoing_init".to_string();
    }

    pub fn incoming(&mut self, call_id: &str, peer: &str) {
        self.active_call_id = Some(call_id.to_string());
        self.active_peer = peer.to_string();
        self.state = "incoming".to_string();
    }

    pub fn set_muted(&mut self, muted: bool) {
        self.muted = muted;
    }

    pub fn apply_call_state(&mut self, call_id: &str, state: &str) {
        self.state = state.to_string();
        if is_terminal_call_state(state) {
            if self.active_call_id.as_deref() == Some(call_id) || self.active_call_id.is_none() {
                self.clear_identity();
            }
        } else {
            self.active_call_id = Some(call_id.to_string());
        }
    }

    pub fn clear(&mut self) {
        self.state = "idle".to_string();
        self.clear_identity();
    }

    pub fn clear_with_state(&mut self, state: &str) {
        self.state = state.to_string();
        self.clear_identity();
    }

    fn clear_identity(&mut self) {
        self.active_call_id = None;
        self.active_peer.clear();
        self.muted = false;
    }
}

fn is_terminal_call_state(state: &str) -> bool {
    matches!(state, "idle" | "released" | "error" | "end")
}
