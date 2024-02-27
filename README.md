# tobi [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
to be or not - Room Presence for Home Assistant utilizing a combination of `motion` and `presence` sensors.

## Installation (with HACS)

1. Go to Home Assistant > HACS > Integrations > Click on tree dot (on top right corner) > Custom repositories \
and fill :
   * **Repository** :  `NinDTendo/tobi`
   * **Category** : `Integration` 

2. Click on `ADD`, restart HA.

## Installation (manual)
1. Download last release.
2. Unzip `tobi` folder into your HomeAssistant : `custom_components`
3. Restart HA

## Configuration
Currently `tobi` can only be set-up using the UI.

## Usage
U'll find out.

## What `tobi` does:
`tobi` reflects the occupancy of a room by utilizing a simple state machine logic, given motion- and presence- sensors.
In particular radar presence sensors like the `ld2410`.
The graphic below illustrates how `tobi` works:
![alt text](https://github.com/NinDTendo/tobi/blob/main/tobi-state_diag.png?raw=true)
