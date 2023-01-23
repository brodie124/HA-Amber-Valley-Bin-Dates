"""Config flow for amber_valley_bin_dates integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

from .amber_valley_bin_dates_scraper import AmberValleyBinDatesScraper

_LOGGER = logging.getLogger(__name__)

STEP_POSTCODE_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("postcode"): str,
    }
)

STEP_SELECTOR_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("property_selector"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(data["host"])

    if not await hub.authenticate(data["username"], data["password"]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for amber_valley_bin_dates."""

    VERSION = 1

    def __init__(self):
        self.bin_date_scraper = AmberValleyBinDatesScraper()
        self.full_property_list = None

    async def async_step_postcode(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Get the postcode"""
        if user_input is None:
            return self.async_show_form(step_id="postcode", data_schema=STEP_POSTCODE_DATA_SCHEMA)

        errors = {}
        self.full_property_list = self.bin_date_scraper.query_properties_by_postcode(user_input['postcode'])

    async def async_step_selector(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Get the property selector"""
        if user_input is None:
            return self.async_show_form(step_id="selector", data_schema=STEP_SELECTOR_DATA_SCHEMA)

        errors = {}
        property_id = self.bin_date_scraper.get_refuse_collection_id(self.full_property_list, user_input['property_selector'])
        if isinstance(property_id, int):
            if property_id == -1:
                errors['property_selector'] = 'property_selector_no_matches'
            elif property_id == 0:
                errors['property_selector'] = 'property_selector_multiple_matches'
        elif not isinstance(property_id, str):
            errors['base'] = "property_selector_unknown"

        refuse_dates = self.bin_date_scraper.query_refuse_dates_by_property_id(property_id)
        if not refuse_dates:
            errors['base'] = 'api_refuse_unknown'

        if len(errors.keys()) > 0:
            return self.async_show_form(step_id="selector", data_schema=STEP_SELECTOR_DATA_SCHEMA, errors=errors)

        return self.async_create_entry(
            title="Amber Valley Bin Dates",
            data={
                "postcode": user_input["postcode"],
                "property_selector": user_input["property_selector"]
            },
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
