"""tobi- 2b||(2b) - Room Presence integration."""
from enum import StrEnum
import logging
from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
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
    registry = entity_registry.async_get(hass)

    config_motion_sensors = config_entry.options["motion_sensors"]
    config_presence_sensors = config_entry.options["presence_sensors"]
    config_allow_re_presence = config_entry.options["allow_re_presence"]

    # Validate + resolve entity registry id to entity_id
    motion_sensors = [ entity_registry.async_validate_entity_id(registry, e) for e in config_motion_sensors ]
    presence_sensors = [ entity_registry.async_validate_entity_id(registry, e) for e in config_presence_sensors ]

    async_add_entities(
        [TobiBinarySensor(hass, unique_id, name, motion_sensors, presence_sensors, config_allow_re_presence)]
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
        allow_re_presence,
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
        self.presence_sensors = presence_sensors
        self.allow_re_presence = allow_re_presence
        self._s1 = True

        self._listeners = []
        self._time = datetime.now()
        self._last_presence = datetime.min
        self._state: STATES = STATES.S0

    def get_initial_state(self) -> STATES:
        if self.get_presence_state():
            self._last_presence = datetime.now()
            return STATES.S2
        if self.get_motion_state():
            return STATES.S1
        return STATES.S0

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on.""" # TODO: add option to report "off" if in S1
        return self._state in [STATES.S1*self._s1, STATES.S2]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "state": self._state,
            "last_triggered": self._time,
        }

    async def async_added_to_hass(self) -> None:
        """Connect listeners when added to hass."""
        self._state = self.get_initial_state()
        self._listeners.append(
            async_track_state_change_event(
                self._hass, self.motion_sensors, self.motion_event_handler
            )
        )
        self._listeners.append(
            async_track_state_change_event(
                self._hass, self.presence_sensors, self.presence_event_handler
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

    async def _motion_handler(self, entity_id, old_state, new_state): # TODO: check change from old_state to new_state
        match self._state:
            case STATES.S0:
                if new_state.state == "on":
                    time_passed_since_last_presence = datetime.now() - self._last_presence
                    if time_passed_since_last_presence.total_seconds() <= 5 and self.get_presence_state():
                        self._state = STATES.S2
                    else:
                        self._state = STATES.S1
                else:
                    return

            case STATES.S1:
                if new_state.state == "off":
                    self._state = STATES.S0
                else:
                    return

            case STATES.S2:
                return

        await self.update_state()

    async def _presence_handler(self, entity_id, old_state, new_state):
        now = datetime.now()
        if new_state.state == "on":
            self._last_presence = now

        match self._state:
            case STATES.S0:
                if not self.allow_re_presence:
                    return

                time_passed = now - self._time
                if time_passed.total_seconds() <= 60 and new_state.state == "on": # TODO: configure re_presence timer
                    self._state = STATES.S2
                    _LOGGER.debug("re presence accepted")
                else:
                    return

            case STATES.S1:
                if new_state.state == "on":
                    self._state = STATES.S2
                else:
                    return

            case STATES.S2:
                if new_state.state == "off":
                    self._state = STATES.S0
                else:
                    return

        await self.update_state()

    async def update_state(self):
        """Update the state of the sensor."""
        self._time = datetime.now()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect listeners on removal."""
        for listener in self._listeners:
            listener()
        self._listeners.clear()

    def get_motion_state(self) -> bool:
        """Return the state of the motion sensors."""
        for entity_id in self.motion_sensors:
            sensor = self._hass.states.get(entity_id)
            if sensor and sensor.state == "on":
                return True
        return False

    def get_presence_state(self) -> bool:
        """Return the state of the presence sensor."""
        for entity_id in self.presence_sensors:
            sensor = self._hass.states.get(entity_id)
            if sensor and sensor.state == "on":
                return True
        return False
