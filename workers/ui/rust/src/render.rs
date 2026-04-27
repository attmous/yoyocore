use crate::framebuffer::{rgb565, Framebuffer};

pub fn render_test_scene(framebuffer: &mut Framebuffer, counter: u64) {
    framebuffer.clear(rgb565(8, 10, 14));

    framebuffer.fill_rect(12, 16, 216, 52, rgb565(34, 48, 70));
    framebuffer.fill_rect(24, 28, 132, 12, rgb565(240, 242, 245));
    framebuffer.fill_rect(24, 48, 86, 8, rgb565(80, 196, 160));

    let progress_width = 32 + ((counter as usize * 17) % 168);
    framebuffer.fill_rect(20, 92, 200, 18, rgb565(18, 24, 34));
    framebuffer.fill_rect(20, 92, progress_width, 18, rgb565(248, 190, 72));

    let button_top = 170 + ((counter as usize * 11) % 42);
    framebuffer.fill_rect(80, button_top, 80, 52, rgb565(22, 116, 138));
    framebuffer.fill_rect(96, button_top + 14, 48, 10, rgb565(230, 250, 248));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scene_changes_with_counter() {
        let mut first = Framebuffer::new(240, 280);
        let mut second = Framebuffer::new(240, 280);

        render_test_scene(&mut first, 1);
        render_test_scene(&mut second, 2);

        assert_ne!(first.as_be_bytes(), second.as_be_bytes());
        assert_eq!(first.pixel(0, 0), rgb565(8, 10, 14));
    }
}
