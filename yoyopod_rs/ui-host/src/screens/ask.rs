use crate::runtime::{RuntimeSnapshot, UiScreen, UiView};
use crate::screens::{chrome, AskViewModel};

pub fn ask_model(snapshot: &RuntimeSnapshot) -> AskViewModel {
    AskViewModel {
        chrome: chrome::chrome(snapshot, "2x Tap = Ask | Hold = Back"),
        title: snapshot.voice.headline.clone(),
        subtitle: snapshot.voice.body.clone(),
        icon_key: "ask".to_string(),
    }
}

pub fn voice_note_model(snapshot: &RuntimeSnapshot) -> AskViewModel {
    AskViewModel {
        chrome: chrome::chrome(snapshot, "2x Tap = Record | Hold = Back"),
        title: if snapshot.voice.capture_in_flight {
            "Recording".to_string()
        } else {
            "Voice Note".to_string()
        },
        subtitle: snapshot.voice.body.clone(),
        icon_key: "microphone".to_string(),
    }
}

pub fn ask_view(snapshot: &RuntimeSnapshot, focus_index: usize) -> UiView {
    UiView {
        screen: UiScreen::Ask,
        title: snapshot.voice.headline.clone(),
        subtitle: snapshot.voice.body.clone(),
        footer: "2x Tap = Ask | Hold = Back".to_string(),
        items: Vec::new(),
        focus_index,
    }
}

pub fn voice_note_view(snapshot: &RuntimeSnapshot, focus_index: usize) -> UiView {
    UiView {
        screen: UiScreen::VoiceNote,
        title: if snapshot.voice.capture_in_flight {
            "Recording".to_string()
        } else {
            "Voice Note".to_string()
        },
        subtitle: snapshot.voice.body.clone(),
        footer: "2x Tap = Record | Hold = Back".to_string(),
        items: Vec::new(),
        focus_index,
    }
}
