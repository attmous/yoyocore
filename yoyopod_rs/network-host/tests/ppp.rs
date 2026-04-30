use std::path::PathBuf;

use yoyopod_network_host::ppp::{
    build_pppd_command, resolve_pppd_binary_with, should_manage_default_route, PppCommandError,
    PppLaunchConfig,
};

#[test]
fn resolve_pppd_binary_uses_usr_sbin_fallback_when_path_omits_pppd() {
    let resolved = resolve_pppd_binary_with(
        |candidate| match candidate {
            "/usr/sbin/pppd" => Some(PathBuf::from("/usr/sbin/pppd")),
            _ => None,
        },
        |_| false,
    );

    assert_eq!(resolved, Some(PathBuf::from("/usr/sbin/pppd")));
}

#[test]
fn build_pppd_command_wraps_with_sudo_for_non_root_launches() {
    let argv = build_pppd_command(&PppLaunchConfig {
        serial_port: "/dev/ttyUSB3".to_string(),
        baud_rate: 115_200,
        pppd_path: PathBuf::from("/usr/sbin/pppd"),
        sudo_path: Some(PathBuf::from("/usr/bin/sudo")),
        is_root: false,
        manage_default_route: true,
    })
    .expect("command should build");

    assert_eq!(argv[0], "/usr/bin/sudo");
    assert_eq!(argv[1], "-n");
    assert_eq!(argv[2], "/usr/sbin/pppd");
    assert!(argv.iter().any(|arg| arg == "defaultroute"));
    assert!(argv.iter().any(|arg| arg == "usepeerdns"));
    assert!(argv
        .iter()
        .any(|arg| arg == "chat -v '' AT OK 'ATD*99#' CONNECT"));
}

#[test]
fn build_pppd_command_fails_for_non_root_launch_without_sudo() {
    let error = build_pppd_command(&PppLaunchConfig {
        serial_port: "/dev/ttyUSB3".to_string(),
        baud_rate: 115_200,
        pppd_path: PathBuf::from("/usr/sbin/pppd"),
        sudo_path: None,
        is_root: false,
        manage_default_route: true,
    })
    .expect_err("sudo should be required");

    assert!(matches!(error, PppCommandError::MissingSudo));
}

#[test]
fn build_pppd_command_skips_default_route_and_peer_dns_when_wifi_owns_uplink() {
    let argv = build_pppd_command(&PppLaunchConfig {
        serial_port: "/dev/ttyUSB3".to_string(),
        baud_rate: 115_200,
        pppd_path: PathBuf::from("/usr/sbin/pppd"),
        sudo_path: None,
        is_root: true,
        manage_default_route: false,
    })
    .expect("command should build");

    assert!(!argv.iter().any(|arg| arg == "defaultroute"));
    assert!(!argv.iter().any(|arg| arg == "usepeerdns"));
}

#[test]
fn non_ppp_default_route_suppresses_default_route_management() {
    let route_output =
        "default via 192.168.178.1 dev wlan0 proto dhcp src 192.168.178.85 metric 50\n";

    assert!(!should_manage_default_route(route_output));
}

#[test]
fn existing_ppp_default_route_keeps_default_route_management() {
    let route_output = "default via 10.64.64.64 dev ppp0\n";

    assert!(should_manage_default_route(route_output));
}
