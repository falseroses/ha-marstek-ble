"""Binary sensor platform for Marstek BLE integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MarstekDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek BLE binary sensors from a config entry."""
    coordinator: MarstekDataUpdateCoordinator = entry.runtime_data

    if coordinator.is_v500:
        async_add_entities(
            [
                MarstekBinarySensor(
                    coordinator,
                    entry,
                    "ac_input_connected",
                    "AC Input Connected",
                    lambda data: data.ac_input_connected,
                    BinarySensorDeviceClass.PLUG,
                ),
                MarstekBinarySensor(
                    coordinator,
                    entry,
                    "ac_output_enabled",
                    "AC Output",
                    lambda data: data.ac_output_enabled,
                    BinarySensorDeviceClass.POWER,
                ),
            ]
        )
        return

    entities = [
        # Note: BLE Connected sensor removed - coordinator doesn't maintain persistent client connection
        # TODO: Add proper connectivity tracking if needed
        MarstekBinarySensor(
            coordinator,
            entry,
            "grid_connected",
            "Grid Connected",
            lambda data: data.grid_connected,
            BinarySensorDeviceClass.POWER,
        ),
        MarstekBinarySensor(
            coordinator,
            entry,
            "wifi_connected",
            "WiFi Connected",
            lambda data: data.wifi_connected,
            BinarySensorDeviceClass.CONNECTIVITY,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        MarstekBinarySensor(
            coordinator,
            entry,
            "mqtt_connected",
            "MQTT Connected",
            lambda data: data.mqtt_connected,
            BinarySensorDeviceClass.CONNECTIVITY,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        MarstekBinarySensor(
            coordinator,
            entry,
            "out1_active",
            "Output 1 Active",
            lambda data: data.out1_active,
            BinarySensorDeviceClass.POWER,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        MarstekBinarySensor(
            coordinator,
            entry,
            "extern1_connected",
            "External 1 Connected",
            lambda data: data.extern1_connected,
            BinarySensorDeviceClass.CONNECTIVITY,
        ),
        MarstekBinarySensor(
            coordinator,
            entry,
            "smart_meter_connected",
            "Smart Meter Connected",
            lambda data: data.smart_meter_connected,
            BinarySensorDeviceClass.CONNECTIVITY,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ]

    async_add_entities(entities)


class MarstekBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Marstek binary sensor."""

    def __init__(
        self,
        coordinator: MarstekDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        value_fn,
        device_class: BinarySensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_has_entity_name = True
        self._value_fn = value_fn
        self._attr_device_class = device_class
        self._attr_entity_category = entity_category
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.coordinator.data is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._value_fn(self.coordinator.data)

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
