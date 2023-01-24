"""Config flow for amber_valley_bin_dates integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult, FlowHandler
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import selector, TextSelector, TextSelectorType, TextSelectorConfig

from .const import DOMAIN

from .amber_valley_bin_dates_scraper import AmberValleyBinDatesScraper

_LOGGER = logging.getLogger(__name__)

STEP_POSTCODE_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("postcode"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="postcode")
        ),
    }
)

STEP_SELECTOR_DATA_SCHEMA = {
}


# @config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for amber_valley_bin_dates."""

    VERSION = 1

    def __init__(self):
        self.postcode = None
        self.bin_date_scraper = AmberValleyBinDatesScraper()
        self.full_property_list = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Get the postcode"""
        _LOGGER.warning("Step User")
        await self.async_set_unique_id("BPIT_AmberValleyBinDates")
        return await self.async_step_postcode(user_input)

    async def async_step_postcode(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Get the postcode"""
        _LOGGER.warning("Step Postcode")
        if user_input is None:
            _LOGGER.warning("Step Postcode - user input is None")
            return self.async_show_form(step_id="postcode", data_schema=STEP_POSTCODE_DATA_SCHEMA)

        _LOGGER.warning("Step Postcode - getting property list")
        self.full_property_list = await self.bin_date_scraper.query_properties_by_postcode(user_input['postcode'])
        _LOGGER.warning("Full property list length: " + str(len(self.full_property_list)))
        if isinstance(self.full_property_list, bool) and not self.full_property_list:
            return self.async_abort(reason="api_unavailable")
        if len(self.full_property_list) < 1:
            _LOGGER.warning("re-showing form with errors")
            errors = { "postcode": "postcode_no_matches" }
            return self.async_show_form(step_id="postcode", data_schema=STEP_POSTCODE_DATA_SCHEMA, errors=errors)

        self.postcode = user_input['postcode']
        _LOGGER.warning("Step Postcode - got property list... showing next step")

        return await self.async_step_selector()

    async def async_step_selector(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Get the property selector"""
        _LOGGER.warning("Step Selector")
        if user_input is None:
            _LOGGER.warning("Step Selector - user input is None")
            _LOGGER.warning("Full property list: " + json.dumps(self.full_property_list))
            STEP_SELECTOR_DATA_SCHEMA['property_selector'] = selector({
                "select": {
                    "options": [x['addressComma'] for x in self.full_property_list]
                }
            })
            return self.async_show_form(step_id="selector", data_schema=vol.Schema(STEP_SELECTOR_DATA_SCHEMA))

        errors = {}
        property_id = self.bin_date_scraper.get_refuse_collection_id(self.full_property_list, user_input['property_selector'])
        if isinstance(property_id, int):
            if property_id == -1:
                errors['property_selector'] = 'property_selector_no_matches'
            elif property_id == 0:
                errors['property_selector'] = 'property_selector_multiple_matches'
        elif not isinstance(property_id, str):
            errors['base'] = "property_selector_unknown"

        refuse_dates = await self.bin_date_scraper.query_refuse_dates_by_property_id(property_id)
        if not refuse_dates:
            errors['base'] = 'api_refuse_unknown'

        if len(errors.keys()) > 0:
            return self.async_show_form(step_id="selector", data_schema=vol.Schema(STEP_SELECTOR_DATA_SCHEMA), errors=errors)


        return self.async_create_entry(
            title="Amber Valley Bin Dates",
            data={
                "postcode": self.postcode,
                "property_selector": user_input['property_selector'],
                "property_uprn": property_id
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
