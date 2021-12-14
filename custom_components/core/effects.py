from typing import Optional

class Effect(object):
    def __init__(
        self,
        code: str,
        name: Optional[str] = None,
        parent: Optional[object] = None,
        is_preset: bool = False,
        is_custom: bool = False
    ) -> None:
        if name is None:
            name = code

        self._code = code
        self._name = name
        self._parent = parent
        self._category = "custom_presets" if is_custom else "default_presets"
        self._is_brightness = parent.is_brightness if parent is not None else None

        if is_preset:
            self._name = "* {}".format(self._name)
        if is_custom:
            self._name = "*{}".format(self._name)

        self._support_entities = parent.support_entities if parent is not None else []

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> Optional[object]:
        return self._parent

    @property
    def code(self) -> str:
        return self._code

    @property
    def category(self) -> str:
        return self._category

    @property
    def is_brightness(self) -> bool:
        return self._is_brightness

    @property
    def is_preset(self) -> bool:
        return self._parent is not None

    @property
    def support_entities(self) -> list:
        return self._support_entities

    def is_support_entity(self, id: str) -> bool:
        return id in self._support_entities

    async def async_brightness_enable(self) -> None:
        self._is_brightness = True

    async def async_append_entity(self, entity: str) -> None:
        self._support_entities.append(entity)

class Effects(object):
    def __init__(self) -> None:
        self._effects = {}

    async def async_append(self, effect: Effect) -> None:
        self._effects[effect.name] = effect

    @property
    def list(self) -> list:
        return list(self._effects.keys())

    @property
    def first(self) -> Optional[Effect]:
        return list(self._effects.values())[0] if len(self._effects) > 0 else None

    def get(self, code: str) -> Optional[Effect]:
        return self._effects[code] if code in self._effects else None

async def async_parse_effects(schema: dict, config: dict) -> Effects:
    effects = Effects()

    if "effects" not in schema or len(schema["effects"]) == 0:
        return effects

    for code in schema["effects"]:
        effect = Effect(code)

        for property in schema["effects"][code]["schema"]["properties"]:
            if property == "brightness":
                await effect.async_brightness_enable()

                continue

            await effect.async_append_entity(property)

        await effects.async_append(effect)

        if code in config["config"]["default_presets"]:
            for preset in config["config"]["default_presets"][code]:
                await effects.async_append(
                    Effect(
                        preset,
                        config["config"]["default_presets"][code][preset]["name"],
                        effect,
                        True
                    )
                )

        if "custom_presets" in config["config"] and code in config["config"]["custom_presets"]:
            for preset in config["config"]["custom_presets"][code]:
                await effects.async_append(
                    Effect(
                        preset,
                        config["config"]["custom_presets"][code][preset]["name"],
                        effect,
                        True,
                        True
                    )
                )

    return effects