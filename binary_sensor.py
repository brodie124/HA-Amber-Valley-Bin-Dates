"""Platform for sensor integration."""
from __future__ import annotations

import json
import logging
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import random
from datetime import datetime, timedelta
from typing import Callable

import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    ATTR_VOLTAGE,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_ILLUMINANCE,
    PERCENTAGE,
)
from homeassistant.core import callback

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


_LAST_REFUSE_DATES = None

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    bin_dates_api = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = BinDatesCoordinator(hass, bin_dates_api)
    await coordinator.async_config_entry_first_refresh()

    async_add_devices([
        DomesticBin(coordinator),
        RecyclingBin(coordinator),
        GardenBin(coordinator),
    ])


class BinDatesCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, bin_dates_api):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Amber Valley Bin Dates Scraper",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=20),
        )
        self.bin_dates_api = bin_dates_api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        async with async_timeout.timeout(30):
            global _LAST_REFUSE_DATES
            _LOGGER.info("Making Amber Valley API call")
            refuse_dates = await self.bin_dates_api.query_refuse_dates_by_property_id()
            _LOGGER.info("Got response from api call")
            _LOGGER.info(refuse_dates)
            if not refuse_dates:
                raise UpdateFailed(f"Error communicating with AV API.")

            self.data = refuse_dates
            _LAST_REFUSE_DATES = refuse_dates


class BinBase(CoordinatorEntity, BinarySensorEntity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, coordinator, bin_type):
        """Pass coordinator to CoordinatorEntity."""
        self.bin_type = bin_type
        self._attr_has_entity_name = True
        self._attr_unique_id = f"AV_{self.bin_type}_Bin"
        self._attr_name = f"{self.bin_type} bin"
        self._attr_is_on = False
        super().__init__(coordinator)

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {
            "name": self.bin_type + " bin"
        }

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if _LAST_REFUSE_DATES is None:
            _LOGGER.error("Coordinator data is type none!")
            return

        self._attr_is_on = _LAST_REFUSE_DATES[self.bin_type].date() == datetime.today().date()
        self.async_write_ha_state()

    def async_will_remove_from_hass(self) -> None:
        _LOGGER.info(f"Removing Amber Valley Bin Date ({self.bin_type}) entity")
        return None


class RecyclingBin(BinBase):
    def __init__(self, coordinator):
        super().__init__(coordinator, "recycling")


class DomesticBin(BinBase):
    def __init__(self, coordinator):
        super().__init__(coordinator, "domestic")


class GardenBin(BinBase):
    def __init__(self, coordinator):
        super().__init__(coordinator, "garden")
