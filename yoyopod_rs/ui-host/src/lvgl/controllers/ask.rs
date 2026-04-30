use anyhow::{anyhow, bail, Result};

use crate::lvgl::{LvglFacade, ScreenController, WidgetId};
use crate::screens::{AskViewModel, ScreenModel};

#[derive(Default)]
pub struct AskController {
    root: Option<WidgetId>,
    title: Option<WidgetId>,
    subtitle: Option<WidgetId>,
    footer: Option<WidgetId>,
    icon: Option<WidgetId>,
}

impl AskController {
    fn ensure_widgets(&mut self, facade: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            self.root = Some(facade.create_root()?);
        }

        let root = self
            .root
            .ok_or_else(|| anyhow!("ask controller missing root widget"))?;

        if self.title.is_none() {
            self.title = Some(facade.create_label(root, "ask_title")?);
        }
        if self.subtitle.is_none() {
            self.subtitle = Some(facade.create_label(root, "ask_subtitle")?);
        }
        if self.footer.is_none() {
            self.footer = Some(facade.create_label(root, "ask_footer")?);
        }
        if self.icon.is_none() {
            self.icon = Some(facade.create_label(root, "ask_icon")?);
        }

        Ok(())
    }
}

impl ScreenController for AskController {
    fn sync(&mut self, facade: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let ask = ask_model(model)?;

        self.ensure_widgets(facade)?;

        if let Some(title) = self.title {
            facade.set_text(title, &ask.title)?;
        }
        if let Some(subtitle) = self.subtitle {
            facade.set_text(subtitle, &ask.subtitle)?;
        }
        if let Some(footer) = self.footer {
            facade.set_text(footer, &ask.chrome.footer)?;
        }
        if let Some(icon) = self.icon {
            facade.set_icon(icon, &ask.icon_key)?;
        }

        Ok(())
    }

    fn teardown(&mut self, facade: &mut dyn LvglFacade) -> Result<()> {
        let root = self.root.take();
        self.title = None;
        self.subtitle = None;
        self.footer = None;
        self.icon = None;
        if let Some(root) = root {
            facade.destroy(root)?;
        }
        Ok(())
    }
}

fn ask_model(model: &ScreenModel) -> Result<&AskViewModel> {
    match model {
        ScreenModel::Ask(ask) | ScreenModel::VoiceNote(ask) => Ok(ask),
        _ => bail!(
            "ask controller received non-ask screen model: {}",
            model.screen().as_str()
        ),
    }
}
