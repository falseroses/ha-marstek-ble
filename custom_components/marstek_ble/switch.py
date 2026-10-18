"""Switch platform for Marstek BLE integration."""
from __future__ import annotations

from typing import Callable

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CMD_AC_INPUT,
    CMD_BUZZER,
    CMD_EPS_MODE,
    CMD_GENERATOR,
    CMD_OUTPUT_CONTROL,
    CMD_V500_AC_OUTPUT,
    DOMAIN,
    FRAME_TYPE_V500_WRITE,
)
from .coordinator import MarstekDataUpdateCoordinator
from .marstek_device import MarstekData

SwitchValueFn = Callable[[MarstekData], bool | None]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek BLE switches from a config entry."""
    coordinator: MarstekDataUpdateCoordinator = entry.runtime_data

    if coordinator.is_v500:
        # Venus E controls do not apply; the V500 has its own AC output command.
        async_add_entities(
            [
                MarstekSwitch(
                    coordinator,
                    entry,
                    "ac_output",
                    "AC Output",
                    CMD_V500_AC_OUTPUT,
                    value_fn=lambda data: data.ac_output_enabled,
                    frame_type=FRAME_TYPE_V500_WRITE,
                    expect_response=False,
                    entity_category=None,
                ),
            ]
        )
        return

    entities = [
        MarstekSwitch(
            coordinator,
            entry,
            "out1_control",
            "Output 1 Control",
            CMD_OUTPUT_CONTROL,
            value_fn=lambda data: data.out1_active,
        ),
        MarstekSwitch(
            coordinator,
            entry,
            "eps_mode",
            "EPS Mode",
            CMD_EPS_MODE,
            value_fn=None,
        ),
        MarstekSwitch(
            coordinator,
            entry,
            "ac_input",
            "AC Input",
            CMD_AC_INPUT,
            value_fn=None,
        ),
        MarstekSwitch(
            coordinator,
            entry,
            "generator",
            "Generator",
            CMD_GENERATOR,
            value_fn=None,
        ),
        MarstekSwitch(
            coordinator,
            entry,
            "buzzer",
            "Buzzer",
            CMD_BUZZER,
            value_fn=None,
        ),
    ]

    async_add_entities(entities)


class MarstekSwitch(CoordinatorEntity[MarstekDataUpdateCoordinator], SwitchEntity):
    """Representation of a Marstek switch."""

    def __init__(
        self,
        coordinator: MarstekDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        cmd: int,
        value_fn: SwitchValueFn | None,
        frame_type: int = 0x23,
        expect_response: bool = True,
        entity_category: EntityCategory | None = EntityCategory.CONFIG,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_has_entity_name = True
        self._cmd = cmd
        self._value_fn = value_fn
        self._frame_type = frame_type
        self._expect_response = expect_response
        self._assumed_state: bool | None = None
        self._attr_entity_category = entity_category
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if await self.coordinator.device.send_command(
            self._cmd,
            b"\x01",
            frame_type=self._frame_type,
            expect_response=self._expect_response,
        ):
            self._assumed_state = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if await self.coordinator.device.send_command(
            self._cmd,
            b"\x00",
            frame_type=self._frame_type,
            expect_response=self._expect_response,
        ):
            self._assumed_state = False
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        return self._current_state()

    @property
    def assumed_state(self) -> bool:
        """Return true if the switch is assumed state."""
        return self._value_fn is None

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.ble_device.address)},
            "connections": {(CONNECTION_BLUETOOTH, self.coordinator.ble_device.address)},
            "name": self.coordinator.device_name,
            "manufacturer": "Marstek",
            "model": self.coordinator.model,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data."""
        self._current_state()
        super()._handle_coordinator_update()

    def _current_state(self) -> bool | None:
        """Return the most recent state, updating from coordinator when possible."""
        if self._value_fn:
            value = self._value_fn(self.coordinator.data)
            if value is not None:
                self._assumed_state = value
        return self._assumed_state
