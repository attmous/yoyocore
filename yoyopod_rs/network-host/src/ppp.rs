use std::path::{Path, PathBuf};
use std::process::Command;

use thiserror::Error;

const PPPD_BINARY_CANDIDATES: [&str; 3] = ["pppd", "/usr/sbin/pppd", "/sbin/pppd"];
const SUDO_BINARY_CANDIDATES: [&str; 3] = ["sudo", "/usr/bin/sudo", "/bin/sudo"];
const CONNECT_CHAT_SCRIPT: &str = "chat -v '' AT OK 'ATD*99#' CONNECT";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PppLaunchConfig {
    pub serial_port: String,
    pub baud_rate: u32,
    pub pppd_path: PathBuf,
    pub sudo_path: Option<PathBuf>,
    pub is_root: bool,
    pub manage_default_route: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PppCommandPlan {
    pub argv: Vec<String>,
    pub manage_default_route: bool,
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum PppCommandError {
    #[error("pppd requires root privileges, but sudo was not found")]
    MissingSudo,
}

pub fn resolve_pppd_binary() -> Option<PathBuf> {
    resolve_pppd_binary_with(
        |candidate| which_path(candidate),
        |candidate| Path::new(candidate).exists(),
    )
}

pub fn resolve_sudo_binary() -> Option<PathBuf> {
    resolve_sudo_binary_with(
        |candidate| which_path(candidate),
        |candidate| Path::new(candidate).exists(),
    )
}

pub fn resolve_pppd_binary_with<F, G>(which: F, exists: G) -> Option<PathBuf>
where
    F: Fn(&str) -> Option<PathBuf>,
    G: Fn(&str) -> bool,
{
    resolve_binary_with(&PPPD_BINARY_CANDIDATES, which, exists)
}

pub fn resolve_sudo_binary_with<F, G>(which: F, exists: G) -> Option<PathBuf>
where
    F: Fn(&str) -> Option<PathBuf>,
    G: Fn(&str) -> bool,
{
    resolve_binary_with(&SUDO_BINARY_CANDIDATES, which, exists)
}

pub fn should_manage_default_route(route_output: &str) -> bool {
    for line in route_output.lines() {
        let tokens: Vec<_> = line.split_whitespace().collect();
        let Some(dev_index) = tokens.iter().position(|token| *token == "dev") else {
            continue;
        };
        let Some(interface) = tokens.get(dev_index + 1) else {
            continue;
        };
        if !interface.starts_with("ppp") {
            return false;
        }
    }
    true
}

pub fn should_manage_default_route_from_system() -> bool {
    let Ok(output) = Command::new("ip")
        .args(["-o", "route", "show", "default"])
        .output()
    else {
        return true;
    };
    if !output.status.success() {
        return true;
    }
    should_manage_default_route(&String::from_utf8_lossy(&output.stdout))
}

pub fn build_command_plan(config: &PppLaunchConfig) -> Result<PppCommandPlan, PppCommandError> {
    Ok(PppCommandPlan {
        argv: build_pppd_command(config)?,
        manage_default_route: config.manage_default_route,
    })
}

pub fn build_pppd_command(config: &PppLaunchConfig) -> Result<Vec<String>, PppCommandError> {
    let mut argv = Vec::new();
    if !config.is_root {
        let sudo_path = config
            .sudo_path
            .as_ref()
            .ok_or(PppCommandError::MissingSudo)?;
        argv.push(sudo_path.display().to_string());
        argv.push("-n".to_string());
    }

    argv.push(config.pppd_path.display().to_string());
    argv.extend([
        config.serial_port.clone(),
        config.baud_rate.to_string(),
        "nodetach".to_string(),
        "noauth".to_string(),
        "persist".to_string(),
        "connect".to_string(),
        CONNECT_CHAT_SCRIPT.to_string(),
    ]);

    if config.manage_default_route {
        argv.push("defaultroute".to_string());
        argv.push("usepeerdns".to_string());
    }

    Ok(argv)
}

fn resolve_binary_with<F, G>(candidates: &[&str], which: F, exists: G) -> Option<PathBuf>
where
    F: Fn(&str) -> Option<PathBuf>,
    G: Fn(&str) -> bool,
{
    for candidate in candidates {
        if let Some(resolved) = which(candidate) {
            return Some(resolved);
        }
        if candidate.starts_with('/') && exists(candidate) {
            return Some(PathBuf::from(candidate));
        }
    }
    None
}

fn which_path(candidate: &str) -> Option<PathBuf> {
    if candidate.contains('/') {
        return Path::new(candidate)
            .exists()
            .then(|| PathBuf::from(candidate));
    }

    let path = std::env::var_os("PATH")?;
    for directory in std::env::split_paths(&path) {
        let candidate_path = directory.join(candidate);
        if candidate_path.exists() {
            return Some(candidate_path);
        }
    }
    None
}
