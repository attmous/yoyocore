"""
PTT (Push-to-Talk) button input adapter for Whisplay HAT.

Maps the single button to PTT press/release actions and optional
navigation actions for menu control.
"""

import time
from collections import defaultdict
from typing import Callable, Optional, Any, List, Dict
from threading import Thread, Event
from loguru import logger

from yoyopy.ui.input.hal import InputHAL, InputAction


class PTTInputAdapter(InputHAL):
    """
    Input adapter for single PTT button (Whisplay HAT).

    The Whisplay HAT has a single button that can be used for:
    - Push-to-talk (press/release events)
    - Navigation via patterns:
      - Single click → SELECT
      - Double click → BACK
      - Long press → Hold for PTT voice input

    This adapter polls the button state via the WhisPlayBoard GPIO interface.
    """

    # Timing constants (in seconds)
    DEBOUNCE_TIME = 0.05       # 50ms debounce
    LONG_PRESS_TIME = 0.8      # 800ms for PTT long press
    DOUBLE_CLICK_TIME = 0.3    # 300ms window for double click
    POLL_RATE = 0.01           # 10ms polling rate

    def __init__(
        self,
        whisplay_device: Optional[object] = None,
        enable_navigation: bool = True,
        simulate: bool = False
    ) -> None:
        """
        Initialize the PTT button input adapter.

        Args:
            whisplay_device: WhisPlayBoard device instance
            enable_navigation: Enable navigation via button patterns (single/double click)
            simulate: Run in simulation mode (no hardware)
        """
        self.device = whisplay_device
        self.enable_navigation = enable_navigation
        self.simulate = simulate

        # Callback storage
        self.callbacks: Dict[InputAction, List[Callable]] = defaultdict(list)

        # Polling thread control
        self.running = False
        self.poll_thread: Optional[Thread] = None
        self.stop_event = Event()

        # Button state tracking
        self.button_pressed = False
        self.press_start_time: Optional[float] = None
        self.last_click_time: Optional[float] = None
        self.long_press_fired = False

        logger.debug(f"PTTInputAdapter initialized (navigation: {enable_navigation})")

    def start(self) -> None:
        """Start PTT button monitoring."""
        if self.running:
            logger.warning("PTTInputAdapter already running")
            return

        self.running = True
        self.stop_event.clear()
        self.poll_thread = Thread(target=self._poll_button, daemon=True)
        self.poll_thread.start()
        logger.info("PTTInputAdapter started")

    def stop(self) -> None:
        """Stop PTT button monitoring."""
        if not self.running:
            return

        self.running = False
        self.stop_event.set()

        if self.poll_thread:
            self.poll_thread.join(timeout=1.0)

        logger.info("PTTInputAdapter stopped")

    def on_action(
        self,
        action: InputAction,
        callback: Callable[[Optional[Any]], None]
    ) -> None:
        """Register callback for an action."""
        self.callbacks[action].append(callback)
        logger.debug(f"Registered callback for action: {action.value}")

    def clear_callbacks(self) -> None:
        """Clear all registered callbacks."""
        self.callbacks.clear()
        logger.debug("Cleared all PTT callbacks")

    def get_capabilities(self) -> List[InputAction]:
        """Return list of supported actions."""
        capabilities = [
            InputAction.PTT_PRESS,
            InputAction.PTT_RELEASE,
        ]

        if self.enable_navigation:
            capabilities.extend([
                InputAction.SELECT,   # Single click
                InputAction.BACK,     # Double click
            ])

        return capabilities

    def _get_button_state(self) -> bool:
        """
        Get the current state of the PTT button.

        Returns:
            True if button is pressed, False otherwise
        """
        if self.simulate or not self.device:
            return False

        try:
            # WhisPlayBoard button state
            # The button is connected to GPIO and can be read via device
            # We check the button attribute if available
            if hasattr(self.device, 'button_pressed'):
                return self.device.button_pressed
            elif hasattr(self.device, 'get_button_state'):
                return self.device.get_button_state()
            else:
                # Fallback: Try to read GPIO directly if available
                import RPi.GPIO as GPIO
                BUTTON_PIN = 26  # Whisplay button GPIO pin
                return GPIO.input(BUTTON_PIN) == GPIO.LOW  # Active low
        except Exception as e:
            logger.error(f"Error reading PTT button state: {e}")
            return False

    def _fire_action(self, action: InputAction, data: Optional[Any] = None) -> None:
        """
        Fire all registered callbacks for an action.

        Args:
            action: Action that occurred
            data: Optional data dict
        """
        callbacks = self.callbacks.get(action, [])
        if callbacks:
            logger.debug(f"PTT action: {action.value}")
            for callback in callbacks:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in PTT callback: {e}")

    def _poll_button(self) -> None:
        """
        Poll PTT button state in a loop.

        Detects:
        - Button press (PTT_PRESS)
        - Button release (PTT_RELEASE)
        - Long press (extended PTT hold)
        - Single click (SELECT) if navigation enabled
        - Double click (BACK) if navigation enabled
        """
        logger.debug("PTT button polling started")

        while not self.stop_event.is_set():
            current_time = time.time()
            current_state = self._get_button_state()
            previous_state = self.button_pressed

            # Button just pressed (transition from False to True)
            if current_state and not previous_state:
                # Debounce
                time.sleep(self.DEBOUNCE_TIME)
                current_state = self._get_button_state()

                if current_state:  # Still pressed after debounce
                    self.button_pressed = True
                    self.press_start_time = current_time
                    self.long_press_fired = False

                    # Fire PTT_PRESS immediately
                    self._fire_action(InputAction.PTT_PRESS, {
                        "timestamp": current_time
                    })
                    logger.trace("PTT button pressed")

            # Button released (transition from True to False)
            elif not current_state and previous_state:
                self.button_pressed = False
                press_duration = 0.0

                if self.press_start_time:
                    press_duration = current_time - self.press_start_time

                # Fire PTT_RELEASE
                self._fire_action(InputAction.PTT_RELEASE, {
                    "timestamp": current_time,
                    "duration": press_duration
                })

                # Handle navigation patterns if enabled and not a long press
                if self.enable_navigation and not self.long_press_fired:
                    # Check for double click
                    if self.last_click_time and \
                       (current_time - self.last_click_time) < self.DOUBLE_CLICK_TIME:
                        # Double click → BACK
                        self._fire_action(InputAction.BACK, {
                            "method": "double_click"
                        })
                        self.last_click_time = None  # Reset to avoid triple click
                    else:
                        # Single click → SELECT
                        # We fire this with a slight delay to allow double-click detection
                        # For now, fire immediately and let double-click override
                        self._fire_action(InputAction.SELECT, {
                            "method": "single_click"
                        })
                        self.last_click_time = current_time

                self.press_start_time = None
                logger.trace(f"PTT button released after {press_duration:.2f}s")

            # Button held down - check for long press
            elif current_state and previous_state:
                if self.press_start_time and not self.long_press_fired:
                    hold_duration = current_time - self.press_start_time
                    if hold_duration >= self.LONG_PRESS_TIME:
                        # Long press detected - useful for voice recording indication
                        logger.debug("PTT long press detected")
                        self.long_press_fired = True
                        # Don't fire SELECT for long press (PTT mode)

            time.sleep(self.POLL_RATE)

        logger.debug("PTT button polling stopped")
