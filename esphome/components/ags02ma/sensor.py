import esphome.codegen as cg
from esphome import automation
import esphome.config_validation as cv
from esphome.components import i2c, sensor
from esphome.const import (
    CONF_ID,
    ICON_RADIATOR,
    ICON_RESTART,
    DEVICE_CLASS_VOLATILE_ORGANIC_COMPOUNDS_PARTS,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_CLASS_MEASUREMENT,
    UNIT_OHM,
    UNIT_PARTS_PER_BILLION,
    CONF_ADDRESS,
    CONF_TVOC,
    CONF_VERSION,
    CONF_MODE,
    CONF_VALUE,
)

CONF_RESISTANCE = "resistance"

DEPENDENCIES = ["i2c"]

ags02ma_ns = cg.esphome_ns.namespace("ags02ma")
AGS02MAComponent = ags02ma_ns.class_("AGS02MAComponent", cg.PollingComponent, i2c.I2CDevice)

# Actions
AGS02MANewI2cAddressAction = ags02ma_ns.class_(
    "AGS02MANewI2cAddressAction", automation.Action
)
AGS02MASetZeroPointAction = ags02ma_ns.class_("AGS02MASetZeroPointAction", automation.Action)

CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(AGS02MAComponent),
            cv.Optional(CONF_TVOC): sensor.sensor_schema(
                unit_of_measurement=UNIT_PARTS_PER_BILLION,
                icon=ICON_RADIATOR,
                accuracy_decimals=0,
                device_class=DEVICE_CLASS_VOLATILE_ORGANIC_COMPOUNDS_PARTS,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_VERSION): sensor.sensor_schema(
                icon=ICON_RESTART,
                entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            ),
            cv.Optional(CONF_RESISTANCE): sensor.sensor_schema(
                unit_of_measurement=UNIT_OHM,
                icon=ICON_RESTART,
                accuracy_decimals=0,
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            ),
        }
    )
    .extend(cv.polling_component_schema("60s"))
    .extend(i2c.i2c_device_schema(0x1A))
)

FINAL_VALIDATE_SCHEMA = i2c.final_validate_device_schema("ags02ma", max_frequency="30khz")


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)

    sens = await sensor.new_sensor(config[CONF_TVOC])
    cg.add(var.set_tvoc(sens))

    if version_config := config.get(CONF_VERSION):
        sens = await sensor.new_sensor(version_config)
        cg.add(var.set_version(sens))

    if resistance_config := config.get(CONF_RESISTANCE):
        sens = await sensor.new_sensor(resistance_config)
        cg.add(var.set_resistance(sens))


AGS02MA_NEW_I2C_ADDRESS_SCHEMA = cv.maybe_simple_value(
    {
        cv.GenerateID(): cv.use_id(AGS02MAComponent),
        cv.Required(CONF_ADDRESS): cv.templatable(cv.i2c_address),
    },
    key=CONF_ADDRESS,
)


@automation.register_action(
    "ags02ma.new_i2c_address",
    AGS02MANewI2cAddressAction,
    AGS02MA_NEW_I2C_ADDRESS_SCHEMA,
)
async def ags02manewi2caddress_to_code(config, action_id, template_arg, args):
    var = cg.new_Pvariable(action_id, template_arg)
    await cg.register_parented(var, config[CONF_ID])
    address = await cg.templatable(config[CONF_ADDRESS], args, int)
    cg.add(var.set_new_address(address))
    return var


AGS02MASetZeroPointActionMode = ags02ma_ns.enum("AGS02MASetZeroPointActionMode")
AGS02MA_SET_ZERO_POINT_ACTION_MODE = {
    "FACTORY_DEFAULT": AGS02MASetZeroPointActionMode.FACTORY_DEFAULT,
    "CURRENT_VALUE": AGS02MASetZeroPointActionMode.CURRENT_VALUE,
    "CUSTOM_VALUE": AGS02MASetZeroPointActionMode.CUSTOM_VALUE,
}

AGS02MA_SET_ZERO_POINT_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.use_id(AGS02MAComponent),
        cv.Required(CONF_MODE): cv.enum(AGS02MA_SET_ZERO_POINT_ACTION_MODE, upper=True),
        cv.Optional(CONF_VALUE, default=0xFFFF): cv.templatable(cv.uint16_t),
    },
)


@automation.register_action(
    "ags02ma.set_zero_point",
    AGS02MASetZeroPointAction,
    AGS02MA_SET_ZERO_POINT_SCHEMA,
)
async def ags02masetzeropoint_to_code(config, action_id, template_arg, args):
    var = cg.new_Pvariable(action_id, template_arg)
    await cg.register_parented(var, config[CONF_ID])
    mode = await cg.templatable(config.get(CONF_MODE), args, enumerate)
    cg.add(var.set_mode(mode))
    value = await cg.templatable(config[CONF_VALUE], args, int)
    cg.add(var.set_value(value))
    return var
