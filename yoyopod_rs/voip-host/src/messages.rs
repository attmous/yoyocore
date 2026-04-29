use serde_json::json;
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MessageRecord {
    pub message_id: String,
    pub peer_sip_address: String,
    pub sender_sip_address: String,
    pub recipient_sip_address: String,
    pub kind: String,
    pub direction: String,
    pub delivery_state: String,
    pub text: String,
    pub local_file_path: String,
    pub mime_type: String,
    pub duration_ms: i32,
    pub unread: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MessageSessionState {
    message_id: String,
    kind: String,
    direction: String,
    delivery_state: String,
    local_file_path: String,
    error: String,
}

impl MessageSessionState {
    pub fn received(message: &MessageRecord) -> Self {
        Self {
            message_id: message.message_id.clone(),
            kind: message.kind.clone(),
            direction: message.direction.clone(),
            delivery_state: message.delivery_state.clone(),
            local_file_path: message.local_file_path.clone(),
            error: String::new(),
        }
    }

    pub fn delivery_changed(
        message_id: &str,
        delivery_state: &str,
        local_file_path: &str,
        error: &str,
    ) -> Self {
        Self {
            message_id: message_id.to_string(),
            kind: String::new(),
            direction: String::new(),
            delivery_state: delivery_state.to_string(),
            local_file_path: local_file_path.to_string(),
            error: error.to_string(),
        }
    }

    pub fn download_completed(message_id: &str, local_file_path: &str) -> Self {
        Self {
            message_id: message_id.to_string(),
            kind: String::new(),
            direction: String::new(),
            delivery_state: "delivered".to_string(),
            local_file_path: local_file_path.to_string(),
            error: String::new(),
        }
    }

    pub fn failed(message_id: &str, reason: &str) -> Self {
        Self {
            message_id: message_id.to_string(),
            kind: String::new(),
            direction: String::new(),
            delivery_state: "failed".to_string(),
            local_file_path: String::new(),
            error: reason.to_string(),
        }
    }

    pub fn payload(&self) -> serde_json::Value {
        json!({
            "message_id": self.message_id,
            "kind": self.kind,
            "direction": self.direction,
            "delivery_state": self.delivery_state,
            "local_file_path": self.local_file_path,
            "error": self.error,
        })
    }
}

#[derive(Debug, Default)]
pub struct OutboundMessageIds {
    ids: HashMap<String, String>,
}

impl OutboundMessageIds {
    pub fn len(&self) -> usize {
        self.ids.len()
    }

    pub fn clear(&mut self) {
        self.ids.clear();
    }

    pub fn translate(&mut self, backend_id: &str, terminal: bool) -> String {
        let client_id = self.ids.get(backend_id).cloned();
        if terminal && client_id.is_some() {
            self.ids.remove(backend_id);
        }
        client_id.unwrap_or_else(|| backend_id.to_string())
    }

    pub fn remember(
        &mut self,
        backend_id: &str,
        client_id: &str,
        label: &str,
    ) -> Result<(), String> {
        let backend_id = backend_id.trim();
        if backend_id.is_empty() {
            return Err(format!("{label} backend returned empty message id"));
        }
        if backend_id != client_id {
            self.ids
                .insert(backend_id.to_string(), client_id.to_string());
        }
        Ok(())
    }
}

pub fn is_terminal_delivery_state(value: &str) -> bool {
    matches!(value, "delivered" | "failed")
}
