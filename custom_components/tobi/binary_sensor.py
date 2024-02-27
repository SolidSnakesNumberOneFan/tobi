"""tobi- 2b||(2b) - Room Presence integration."""
from enum import StrEnum
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize tobi config entry."""
    name = config_entry.title
    unique_id = config_entry.entry_id

    _motion_sensors = config_entry.options["motion_sensors"]
    _presence_sensors = config_entry.options["presence_sensors"]
    _LOGGER.debug("motion_sensors: %s", _motion_sensors)
    # Validate + resolve entity registry id to entity_id
    registry = er.async_get(hass)
    motion_sensors = [er.async_validate_entity_id(registry, e) for e in _motion_sensors]
    presence_sensors = [
        er.async_validate_entity_id(registry, e) for e in _presence_sensors
    ]

    async_add_entities(
        [TobiBinarySensor(hass, unique_id, name, motion_sensors, presence_sensors)]
    )


class STATES(StrEnum):
    """Possible states of the tobi binary sensor."""

    S0 = "vacant"
    S1 = "motion"
    S2 = "occupied"


class TobiBinarySensor(BinarySensorEntity):
    """Representation of a tobi binary sensor."""

    def __init__(
        self,
        hass,
        unique_id: str,
        name: str,
        motion_sensors,
        presence_sensors,
    ) -> None:
        """Initialize the tobi binary sensor."""
        self._hass = hass
        # self._wrapped_entity_id = wrapped_entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        self._attr_should_poll = False
        self._attr_available = True

        self.motion_sensors = motion_sensors
        self.presence_sensor = presence_sensors

        self._state: STATES = STATES.S0
        self._listeners = []

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        """Return the class of this entity."""
        return self._attr_device_class

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._state in [STATES.S1, STATES.S2]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "state": self._state,
            "motion_sensors": self.motion_sensors,
            "presence_sensors": self.presence_sensor,
        }

    async def async_added_to_hass(self) -> None:
        """Connect listeners when added to hass."""
        self._listeners.append(
            async_track_state_change_event(
                self._hass, self.motion_sensors, self.motion_event_handler
            )
        )
        self._listeners.append(
            async_track_state_change_event(
                self._hass, self.presence_sensor, self.presence_event_handler
            )
        )

    async def motion_event_handler(self, event):
        """Handle motion events."""
        _entity_id = event.data.get("entity_id")
        _old_state = event.data.get("old_state")
        _new_state = event.data.get("new_state")
        await self._motion_handler(_entity_id, _old_state, _new_state)

    async def presence_event_handler(self, event):
        """Handle presence events."""
        _entity_id = event.data.get("entity_id")
        _old_state = event.data.get("old_state")
        _new_state = event.data.get("new_state")
        await self._presence_handler(_entity_id, _old_state, _new_state)

    async def _motion_handler(self, entity_id, old_state, new_state):
        match self._state:
            case STATES.S0:
                if new_state.state == "on":
                    self._state = STATES.S1
            case STATES.S1:
                if new_state.state == "off":
                    self._state = STATES.S0
            case STATES.S2:
                pass
        await self.update_state()

    async def _presence_handler(self, entity_id, old_state, new_state):
        match self._state:
            case STATES.S0:
                pass
            case STATES.S1:
                if new_state.state == "on":
                    self._state = STATES.S2
            case STATES.S2:
                if new_state.state == "off":
                    self._state = STATES.S0
        await self.update_state()

    async def update_state(self):
        """Update the state of the sensor."""
        match self._state:
            case STATES.S0:
                if self.get_motion_state():
                    self._state = STATES.S1
            case STATES.S1:
                if self.get_presence_state():
                    self._state = STATES.S2
            case STATES.S2:
                if not self.get_presence_state():
                    self._state = STATES.S0
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect listeners on removal."""
        for listener in self._listeners:
            listener()
        self._listeners.clear()

    def get_motion_state(self):
        """Return the state of the motion sensors."""
        for sensor in self.motion_sensors:
            if self._hass.states.get(sensor).state == "on":
                return True
        return False

    def get_presence_state(self):
        """Return the state of the presence sensor."""
        for sensor in self.presence_sensor:
            if self._hass.states.get(sensor).state == "on":
                return True
        return False
