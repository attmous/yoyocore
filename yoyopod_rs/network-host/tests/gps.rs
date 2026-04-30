use yoyopod_network_host::at::{
    parse_carrier, parse_registration, parse_signal_quality, CarrierInfo, SignalInfo,
};
use yoyopod_network_host::gps::{parse_cgpsinfo, GpsFix};

#[test]
fn parse_cgpsinfo_returns_decimal_fix_and_telemetry() {
    let fix = parse_cgpsinfo("+CGPSINFO: 4852.4300,N,00221.1300,E,130426,120000.0,35.0,0.5,\nOK")
        .expect("gps fix should parse");

    assert!((fix.lat - 48.873_833).abs() < 0.000_1);
    assert!((fix.lng - 2.352_166).abs() < 0.000_1);
    assert_eq!(
        fix,
        GpsFix {
            lat: fix.lat,
            lng: fix.lng,
            altitude: 35.0,
            speed: 0.5,
            timestamp: None,
        }
    );
}

#[test]
fn parse_cgpsinfo_returns_none_for_no_fix_payload() {
    assert_eq!(parse_cgpsinfo("+CGPSINFO: ,,,,,,,,\nOK"), None);
}

#[test]
fn parse_cgpsinfo_applies_southern_and_western_hemisphere_signs() {
    let fix = parse_cgpsinfo("+CGPSINFO: 3351.1200,S,15112.3400,W,130426,120000.0,12.5,1.2,\nOK")
        .expect("gps fix should parse");

    assert!(fix.lat < 0.0);
    assert!(fix.lng < 0.0);
    assert_eq!(fix.altitude, 12.5);
    assert_eq!(fix.speed, 1.2);
}

#[test]
fn signal_bars_follow_python_thresholds() {
    let cases = [
        (SignalInfo { csq: 0 }, 0),
        (SignalInfo { csq: 5 }, 1),
        (SignalInfo { csq: 12 }, 2),
        (SignalInfo { csq: 20 }, 3),
        (SignalInfo { csq: 28 }, 4),
        (SignalInfo { csq: 99 }, 0),
    ];

    for (signal, expected_bars) in cases {
        assert_eq!(
            signal.bars(),
            expected_bars,
            "unexpected bars for csq {}",
            signal.csq
        );
    }
}

#[test]
fn parse_signal_quality_defaults_to_not_detectable_when_missing() {
    assert_eq!(parse_signal_quality("ERROR"), SignalInfo { csq: 99 });
}

#[test]
fn parse_carrier_maps_known_access_technologies() {
    assert_eq!(
        parse_carrier("+COPS: 0,0,\"T-Mobile\",7\nOK"),
        CarrierInfo {
            carrier: "T-Mobile".to_string(),
            network_type: "4G".to_string(),
        }
    );
    assert_eq!(
        parse_carrier("+COPS: 0,0,\"Carrier\",2\nOK"),
        CarrierInfo {
            carrier: "Carrier".to_string(),
            network_type: "3G".to_string(),
        }
    );
    assert_eq!(
        parse_carrier("+COPS: 0,0,\"Carrier\",0\nOK"),
        CarrierInfo {
            carrier: "Carrier".to_string(),
            network_type: "2G".to_string(),
        }
    );
}

#[test]
fn parse_registration_treats_home_and_roaming_as_registered() {
    assert!(parse_registration("+CEREG: 0,1\nOK"));
    assert!(parse_registration("+CEREG: 0,5\nOK"));
    assert!(!parse_registration("+CEREG: 0,0\nOK"));
}
