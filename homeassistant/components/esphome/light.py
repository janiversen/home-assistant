"""Support for ESPHome lights."""
from __future__ import annotations

from typing import Any

from aioesphomeapi import LightInfo, LightState

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    ATTR_WHITE_VALUE,
    FLASH_LONG,
    FLASH_SHORT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    SUPPORT_EFFECT,
    SUPPORT_FLASH,
    SUPPORT_TRANSITION,
    SUPPORT_WHITE_VALUE,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.color as color_util

from . import EsphomeEntity, esphome_state_property, platform_async_setup_entry

FLASH_LENGTHS = {FLASH_SHORT: 2, FLASH_LONG: 10}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up ESPHome lights based on a config entry."""
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        component_key="light",
        info_type=LightInfo,
        entity_type=EsphomeLight,
        state_type=LightState,
    )


# https://github.com/PyCQA/pylint/issues/3150 for all @esphome_state_property
# Pylint gets confused with the EsphomeEntity generics -> let mypy handle member checking
# pylint: disable=invalid-overridden-method,no-member


class EsphomeLight(EsphomeEntity[LightInfo, LightState], LightEntity):
    """A light implementation for ESPHome."""

    @esphome_state_property
    def is_on(self) -> bool | None:  # type: ignore[override]
        """Return true if the light is on."""
        return self._state.state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data: dict[str, Any] = {"key": self._static_info.key, "state": True}
        if ATTR_HS_COLOR in kwargs:
            hue, sat = kwargs[ATTR_HS_COLOR]
            red, green, blue = color_util.color_hsv_to_RGB(hue, sat, 100)
            data["rgb"] = (red / 255, green / 255, blue / 255)
        if ATTR_FLASH in kwargs:
            data["flash_length"] = FLASH_LENGTHS[kwargs[ATTR_FLASH]]
        if ATTR_TRANSITION in kwargs:
            data["transition_length"] = kwargs[ATTR_TRANSITION]
        if ATTR_BRIGHTNESS in kwargs:
            data["brightness"] = kwargs[ATTR_BRIGHTNESS] / 255
        if ATTR_COLOR_TEMP in kwargs:
            data["color_temperature"] = kwargs[ATTR_COLOR_TEMP]
        if ATTR_EFFECT in kwargs:
            data["effect"] = kwargs[ATTR_EFFECT]
        if ATTR_WHITE_VALUE in kwargs:
            data["white"] = kwargs[ATTR_WHITE_VALUE] / 255
        await self._client.light_command(**data)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        data: dict[str, Any] = {"key": self._static_info.key, "state": False}
        if ATTR_FLASH in kwargs:
            data["flash_length"] = FLASH_LENGTHS[kwargs[ATTR_FLASH]]
        if ATTR_TRANSITION in kwargs:
            data["transition_length"] = kwargs[ATTR_TRANSITION]
        await self._client.light_command(**data)

    @esphome_state_property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return round(self._state.brightness * 255)

    @esphome_state_property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the hue and saturation color value [float, float]."""
        return color_util.color_RGB_to_hs(
            self._state.red * 255, self._state.green * 255, self._state.blue * 255
        )

    @esphome_state_property
    def color_temp(self) -> float | None:  # type: ignore[override]
        """Return the CT color value in mireds."""
        return self._state.color_temperature

    @esphome_state_property
    def white_value(self) -> int | None:
        """Return the white value of this light between 0..255."""
        return round(self._state.white * 255)

    @esphome_state_property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self._state.effect

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        flags = SUPPORT_FLASH
        if self._static_info.supports_brightness:
            flags |= SUPPORT_BRIGHTNESS
            flags |= SUPPORT_TRANSITION
        if self._static_info.supports_rgb:
            flags |= SUPPORT_COLOR
        if self._static_info.supports_white_value:
            flags |= SUPPORT_WHITE_VALUE
        if self._static_info.supports_color_temperature:
            flags |= SUPPORT_COLOR_TEMP
        if self._static_info.effects:
            flags |= SUPPORT_EFFECT
        return flags

    @property
    def effect_list(self) -> list[str]:
        """Return the list of supported effects."""
        return self._static_info.effects

    @property
    def min_mireds(self) -> float:  # type: ignore[override]
        """Return the coldest color_temp that this light supports."""
        return self._static_info.min_mireds

    @property
    def max_mireds(self) -> float:  # type: ignore[override]
        """Return the warmest color_temp that this light supports."""
        return self._static_info.max_mireds
