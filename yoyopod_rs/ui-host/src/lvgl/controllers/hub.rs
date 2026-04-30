use anyhow::{anyhow, bail, Result};

use crate::lvgl::chrome;
use crate::lvgl::{LvglFacade, ScreenController, WidgetId};
use crate::screens::ScreenModel;

#[derive(Default)]
pub struct HubController {
    root: Option<WidgetId>,
    title: Option<WidgetId>,
}

impl HubController {
    fn ensure_widgets(&mut self, facade: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            self.root = Some(facade.create_root()?);
        }
        if self.title.is_none() {
            let root = self
                .root
                .ok_or_else(|| anyhow!("hub controller missing root widget"))?;
            self.title = Some(facade.create_label(root, "hub_title")?);
        }
        Ok(())
    }
}

impl ScreenController for HubController {
    fn sync(&mut self, facade: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let ScreenModel::Hub(model) = model else {
            bail!(
                "hub controller received non-hub screen model: {}",
                model.screen().as_str()
            );
        };

        self.ensure_widgets(facade)?;

        if let Some(title) = self.title {
            facade.set_text(title, chrome::focused_hub_title(model))?;
        }

        Ok(())
    }

    fn teardown(&mut self, facade: &mut dyn LvglFacade) -> Result<()> {
        let root = self.root.take();
        self.title = None;
        if let Some(root) = root {
            facade.destroy(root)?;
        }
        Ok(())
    }
}
