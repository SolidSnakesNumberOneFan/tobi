"""The to be or not - Room Presence integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up to be or not - Room Presence from a config entry."""
    # TODO Optionally store an object for your platforms to access
    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ...

    # TODO Optionally validate config entry options before setting up platform

    await hass.config_entries.async_forward_entry_setups(
        entry, (Platform.BINARY_SENSOR,)
    )

    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # await hass.config_entries.async_forward_entry_unload(entry, (Platform.BINARY_SENSOR,))
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, (Platform.BINARY_SENSOR,)
    ):
        # hass.data[DOMAIN].pop(entry.entry_id)
        pass

    return unload_ok
