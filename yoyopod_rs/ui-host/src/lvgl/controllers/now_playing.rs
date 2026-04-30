use anyhow::{anyhow, bail, Result};

use crate::lvgl::{LvglFacade, ScreenController, WidgetId};
use crate::screens::{NowPlayingViewModel, ScreenModel};

#[derive(Default)]
pub struct NowPlayingController {
    root: Option<WidgetId>,
    title: Option<WidgetId>,
    artist: Option<WidgetId>,
    state: Option<WidgetId>,
    progress: Option<WidgetId>,
    footer: Option<WidgetId>,
}

impl NowPlayingController {
    fn ensure_widgets(&mut self, facade: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            self.root = Some(facade.create_root()?);
        }

        let root = self
            .root
            .ok_or_else(|| anyhow!("now-playing controller missing root widget"))?;

        if self.title.is_none() {
            self.title = Some(facade.create_label(root, "now_playing_title")?);
        }
        if self.artist.is_none() {
            self.artist = Some(facade.create_label(root, "now_playing_artist")?);
        }
        if self.state.is_none() {
            self.state = Some(facade.create_label(root, "now_playing_state")?);
        }
        if self.progress.is_none() {
            self.progress = Some(facade.create_label(root, "now_playing_progress")?);
        }
        if self.footer.is_none() {
            self.footer = Some(facade.create_label(root, "now_playing_footer")?);
        }

        Ok(())
    }
}

impl ScreenController for NowPlayingController {
    fn sync(&mut self, facade: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let now_playing = now_playing_model(model)?;
        let progress_value = now_playing.progress_permille.clamp(0, 1000);

        self.ensure_widgets(facade)?;

        if let Some(title) = self.title {
            facade.set_text(title, &now_playing.title)?;
        }
        if let Some(artist) = self.artist {
            facade.set_text(artist, &now_playing.artist)?;
        }
        if let Some(state) = self.state {
            facade.set_text(state, &now_playing.state_text)?;
        }
        if let Some(progress) = self.progress {
            facade.set_progress(progress, progress_value)?;
        }
        if let Some(footer) = self.footer {
            facade.set_text(footer, &now_playing.chrome.footer)?;
        }

        Ok(())
    }

    fn teardown(&mut self, facade: &mut dyn LvglFacade) -> Result<()> {
        let root = self.root.take();
        self.title = None;
        self.artist = None;
        self.state = None;
        self.progress = None;
        self.footer = None;
        if let Some(root) = root {
            facade.destroy(root)?;
        }
        Ok(())
    }
}

fn now_playing_model(model: &ScreenModel) -> Result<&NowPlayingViewModel> {
    match model {
        ScreenModel::NowPlaying(now_playing) => Ok(now_playing),
        _ => bail!(
            "now-playing controller received non-now-playing screen model: {}",
            model.screen().as_str()
        ),
    }
}
