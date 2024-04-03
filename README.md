# AllTalkTTS Home Assistant Integration

AllTalk is an updated version of the Coqui_tts extension for
Text Generation web UI.

## Installation

### AllTalkTTS

Firstly you must have working instance of AllTalkTTS server running.
Follow instructions in the [AllTalkTTS](https://github.com/erew123/alltalk_tts) repository.

### Home Assistant integration

To use it, copy the `alltalktts` folder inside your `config/custom_components`
folder on your home assistant installation.

## Configuration

Add following lines to your Home Assistant configuration:

```yaml
tts:
  - platform: alltalktts
    host: <host>
    port: <port>
```

At the moment integration chooses random voice for every TTS because
I like variety. If you want to add option to choose specific voice,
I am open to PRs.

## Copyrights

Author: Dr Serge Victor

This software is loosely based on concept provided by Markus Pöschl
in his [PicoTTS Remote](https://github.com/Poeschl/Remote-PicoTTS)
custom component.
