"""The amber_valley_bin_dates integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# from amber_valley_bin_dates_scraper import AmberValleyBinDatesScraper
from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up amber_valley_bin_dates from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = AmberValleyBinDatesScraper()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


# class BinDatesCoordinate(DataUpdateCoordinator):
#     """My custom coordinator."""
#
#     def __init__(self, hass, bin_dates_api):
#         """Initialize my coordinator."""
#         super().__init__(
#             hass,
#             _LOGGER,
#             # Name of the data. For logging purposes.
#             name="Amber Valley Bin Dates Scraper",
#             # Polling interval. Will only be polled if there are subscribers.
#             update_interval=timedelta(seconds=500),
#         )
#         self.bin_dates_api = bin_dates_api
#
#     async def _async_update_data(self):
#         """Fetch data from API endpoint.
#
#         This is the place to pre-process the data to lookup tables
#         so entities can quickly look up their data.
#         """
#         try:
#             # Note: asyncio.TimeoutError and aiohttp.ClientError are already
#             # handled by the data update coordinator.
#             async with async_timeout.timeout(10):
#                 # Grab active context variables to limit data required to be fetched from API
#                 # Note: using context is not required if there is no need or ability to limit
#                 # data retrieved from API.
#                 listening_idx = set(self.async_contexts())
#                 return await self.bin_dates_api.fetch_data(listening_idx)
#         except ApiAuthError as err:
#             # Raising ConfigEntryAuthFailed will cancel future updates
#             # and start a config flow with SOURCE_REAUTH (async_step_reauth)
#             raise ConfigEntryAuthFailed from err
#         except ApiError as err:
#             raise UpdateFailed(f"Error communicating with API: {err}")
#