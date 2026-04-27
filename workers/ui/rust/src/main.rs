mod framebuffer;
mod input;
mod protocol;
mod render;

use anyhow::Result;
use clap::{Parser, ValueEnum};

#[derive(Debug, Clone, Copy, ValueEnum)]
enum HardwareMode {
    Mock,
    Whisplay,
}

#[derive(Debug, Parser)]
#[command(name = "yoyopod-rust-ui-poc")]
#[command(about = "Whisplay-only Rust UI hardware I/O proof of concept")]
struct Args {
    #[arg(long, value_enum, default_value_t = HardwareMode::Mock)]
    hardware: HardwareMode,
}

fn main() -> Result<()> {
    let args = Args::parse();
    eprintln!("yoyopod-rust-ui-poc starting hardware={:?}", args.hardware);

    let ready = protocol::Envelope::event(
        "ui.ready",
        serde_json::json!({
            "width": 240,
            "height": 280,
            "hardware": format!("{:?}", args.hardware).to_lowercase(),
        }),
    );
    print!("{}", String::from_utf8(ready.encode()?)?);
    Ok(())
}
