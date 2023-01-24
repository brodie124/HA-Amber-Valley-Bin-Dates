"""The amber_valley_bin_dates integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .amber_valley_bin_dates_scraper import AmberValleyBinDatesScraper
from .const import DOMAIN


PLATFORMS: list[str] = [Platform.BINARY_SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up amber_valley_bin_dates from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_scraper = AmberValleyBinDatesScraper()
    api_scraper.configPostcode = entry.data['postcode']
    api_scraper.configUprn = entry.data['property_uprn']
    hass.data[DOMAIN][entry.entry_id] = api_scraper

    hass.async_create_task(hass.config_entries.async_forward_entry_setups(entry, PLATFORMS))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
