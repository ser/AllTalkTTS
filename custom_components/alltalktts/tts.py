"""Support for the TTS speech service."""
import logging

import asyncio
import aiohttp
import random
import async_timeout
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.components.tts import CONF_LANG, PLATFORM_SCHEMA, Provider, Voice
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from aiohttp import FormData

_LOGGER = logging.getLogger(__name__)

SUPPORT_LANGUAGES = ['ar', 'cs', 'de', 'en', 'es', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'pl', 'pt', 'ru', 'tr', 'zh-cn']
SUPPORT_VOICES = ['random']

DEFAULT_LANG = "en"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 7851
DEFAULT_VOICE = "random"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

def get_engine(hass, config, discovery_info=None):
    """Set up TTS speech component."""
    return AlltalkProvider(hass, config[CONF_LANG], config[CONF_HOST], config[CONF_PORT])



class AlltalkProvider(Provider):
    """The TTS API provider."""

    def __init__(self, hass, lang, host, port):
        """Initialize TTS provider."""
        self._hass = hass
        self._lang = lang
        self._host = host
        self._port = port
        self.name = "AllTTS (Remote)"

    @property
    def default_language(self):
        """Return the default language."""
        return self._lang

    @property
    def supported_languages(self):
        """Return list of supported languages."""
        return SUPPORT_LANGUAGES

    @callback
    async def async_get_supported_voices(self, lang: str) -> list[Voice] | None:
        """Return the all voices."""
        websession = async_get_clientsession(self._hass)

        try:
            with async_timeout.timeout(5):
                url = "http://{}:{}/api/voices".format(self._host, self._port)

                request = await websession.get(url)

                if request.status != 200:
                    _LOGGER.error(
                        "Error %d on load url %s", request.status, request.url
                    )
                    return None
                data = await request.json()
                #_LOGGER.error(f"{data}")

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Timeout for TTS API")
            return None

        if data:
            return [Voice(voice, voice) for voice in data['voices']]
        return None


    async def async_get_tts_audio(self, message, language, options=None):
        """Load TTS using a remote server."""
        websession = async_get_clientsession(self._hass)

        try:
            # we need to have two different random voices
            voices = await self.async_get_supported_voices(language)
            voice_1 = random.choice(voices)
            voices.remove(voice_1)
            voice_2 = random.choice(voices)

            #_LOGGER.error(f"{random.choice(voices['voices'])}")
            with async_timeout.timeout(15):
                url = "http://{}:{}/api/tts-generate".format(self._host, self._port)
                formdata = FormData()
                formdata.add_field("text_input", message)
                formdata.add_field("language", language)
                formdata.add_field("text_filtering", "standard")
                formdata.add_field("output_file_timestamp", "true")
                formdata.add_field("autoplay", "false")
                formdata.add_field("character_voice_gen", f"{voice_1.name}")
                formdata.add_field("narrator_enabled", "true")
                formdata.add_field("narrator_voice_gen", f"{voice_2.name}")
                formdata.add_field("text_not_inside", 'character')
                formdata.add_field("output_file_name", 'ha')
                formdata.add_field("autoplay_volume", "0.8")
                #_LOGGER.error(f"{formdata()}")

                request = await websession.post(url, data=formdata)

                if request.status != 200:
                    _LOGGER.error(
                        "Error %d on load url %s, %s", request.status, request.url, await request.text()
                    )
                    return (None, None)

                ttsdata = await request.json()
                #_LOGGER.debug(f"{ttsdata}")

                # generate-success means we must expect wave file on the location
                if ttsdata["status"] == "generate-success":
                    async with websession.get(ttsdata['output_file_url']) as r:
                            return ("wav", await r.read())

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Timeout (15) for TTS API")
            return (None, None)

        except Exception as e:
            _LOGGER.error(f"{e}")
            return (None, None)

        return (None, None)
