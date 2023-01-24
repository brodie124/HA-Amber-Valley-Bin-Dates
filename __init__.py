"""The amber_valley_bin_dates integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta, datetime

import async_timeout
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity, UpdateFailed

from .amber_valley_bin_dates_scraper import AmberValleyBinDatesScraper
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up amber_valley_bin_dates from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = AmberValleyBinDatesScraper()

    hass.states.async_set('amber_valley_bin_dates.DomesticWasteDate', '')
    hass.states.async_set('amber_valley_bin_dates.RecyclingWasteDate', '')
    hass.states.async_set('amber_valley_bin_dates.GardenWasteDate', '')

    hass.states.async_set('amber_valley_bin_dates.DomesticWasteIsToday', False)
    hass.states.async_set('amber_valley_bin_dates.RecyclingWasteIsToday', False)
    hass.states.async_set('amber_valley_bin_dates.GardenWasteIsToday', False)

    api_scraper = AmberValleyBinDatesScraper()
    api_scraper.configPostcode = entry.data['postcode']
    api_scraper.configUprn = entry.data['property_uprn']
    hass.data[DOMAIN][entry.entry_id] = api_scraper

    coordinator = BinDatesCoordinator(hass, api_scraper)
    await coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # if unload_ok := await hass.config_entries.async_unload(entry.entry_id):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class BinDatesCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, bin_dates_api: AmberValleyBinDatesScraper):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Amber Valley Bin Dates Scraper",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=60),
        )
        self.bin_dates_api = bin_dates_api
        self.data = {
            "state": False
        }

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        async with async_timeout.timeout(30):
            # Grab active context variables to limit data required to be fetched from API
            # Note: using context is not required if there is no need or ability to limit
            # data retrieved from API.

            refuse_dates = await self.bin_dates_api.query_refuse_dates_by_property_id()
            if not refuse_dates:
                raise UpdateFailed(f"Error communicating with AV API.")

            self.hass.states.async_set('amber_valley_bin_dates.DomesticWasteDate', refuse_dates['domestic'])
            self.hass.states.async_set('amber_valley_bin_dates.RecyclingWasteDate', refuse_dates['recycling'])
            self.hass.states.async_set('amber_valley_bin_dates.GardenWasteDate', refuse_dates['garden'])

            self.hass.states.async_set(
                'amber_valley_bin_dates.DomesticWasteIsToday',
                refuse_dates['domestic'].date() == datetime.today().date())
            self.hass.states.async_set(
                'amber_valley_bin_dates.RecyclingWasteIsToday',
                refuse_dates['recycling'].date() == datetime.today().date())
            self.hass.states.async_set(
                'amber_valley_bin_dates.GardenWasteIsToday',
                refuse_dates['garden'].date() == datetime.today().date())


class DomesticBinEntity(CoordinatorEntity, BinarySensorEntity):
    """An entity using CoordinatorEntity."""
    def __init__(self, coordinator):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data["state"]
        self.async_write_ha_state()


class RecyclingBinEntity(CoordinatorEntity, BinarySensorEntity):
    """An entity using CoordinatorEntity."""
    def __init__(self, coordinator):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data["state"]
        self.async_write_ha_state()


class GardenBinEntity(CoordinatorEntity, BinarySensorEntity):
    """An entity using CoordinatorEntity."""
    def __init__(self, coordinator):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data["state"]
        self.async_write_ha_state()