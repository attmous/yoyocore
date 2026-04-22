#!/usr/bin/env python3
"""
Generate test audio files for YoYoPod.

Creates simple WAV files with different tones for testing audio playback.
"""

import wave
import struct
import math
from pathlib import Path


def generate_tone(
    filename: Path,
    frequency: float = 440.0,
    duration: float = 1.0,
    sample_rate: int = 44100,
    amplitude: float = 0.5
):
    """
    Generate a simple sine wave tone as a WAV file.

    Args:
        filename: Output file path
        frequency: Frequency in Hz (default 440Hz = A4)
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0.0 to 1.0)
    """
    num_samples = int(sample_rate * duration)

    # Generate samples
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = amplitude * math.sin(2 * math.pi * frequency * t)
        # Convert to 16-bit PCM
        sample_int = int(sample * 32767)
        samples.append(sample_int)

    # Write WAV file
    with wave.open(str(filename), 'w') as wav_file:
        # Set parameters: nchannels, sampwidth, framerate, nframes, comptype, compname
        wav_file.setparams((1, 2, sample_rate, num_samples, 'NONE', 'not compressed'))

        # Write samples
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))

    print(f"Generated {filename.name} ({frequency}Hz, {duration}s)")


def main():
    """Generate test audio files."""
    # Create sounds directory
    sounds_dir = Path("assets/sounds")
    sounds_dir.mkdir(parents=True, exist_ok=True)

    print("Generating test audio files...")

    # Beep sound (440Hz A4 note, 0.5 seconds)
    generate_tone(
        sounds_dir / "beep.wav",
        frequency=440.0,
        duration=0.5,
        amplitude=0.3
    )

    # Start sound (ascending notes)
    generate_tone(
        sounds_dir / "startup.wav",
        frequency=523.25,  # C5
        duration=0.3,
        amplitude=0.3
    )

    # Success sound (high tone)
    generate_tone(
        sounds_dir / "success.wav",
        frequency=659.25,  # E5
        duration=0.4,
        amplitude=0.3
    )

    # Error sound (low tone)
    generate_tone(
        sounds_dir / "error.wav",
        frequency=220.0,  # A3
        duration=0.6,
        amplitude=0.3
    )

    print(f"\n✓ Generated {len(list(sounds_dir.glob('*.wav')))} test audio files")
    print(f"Location: {sounds_dir.absolute()}")


if __name__ == "__main__":
    main()
