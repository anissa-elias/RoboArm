# Wiring guide

Build from these three files together:

| File | Use it for |
|---|---|
| [carrier/carrier_layout.pdf](carrier/carrier_layout.pdf) | Where every part goes on the perfboard |
| [carrier/wire_list.csv](carrier/wire_list.csv) | Every wire and solder bridge on the board, by hole |
| [carrier/mega_plug.csv](carrier/mega_plug.csv) | What each pin of the Mega plug connects to |

The full schematic is [output/roboarm_schematic.pdf](output/roboarm_schematic.pdf). Holes are named by column letter and row number, seen from the component side.

## Before you start

- Check the TMC2209 pin names on your modules against the [BIGTREETECH pin table](https://global.bttwiki.com/TMC2209.html). This plan assumes EN, MS1, MS2, UART, UART, CLK, STEP, DIR on the left and VM, GND, A2, A1, B1, B2, VIO, GND on the right.
- Count your perfboard. The layout needs 24 x 30 holes. If yours is different, change `COLS`, `ROWS` and the positions in `carrier/generate_carrier.py`, and do not adapt it by hand.
- Check the board's mounting holes against the base standoffs, which are 64 x 84 mm apart.
- Keep motor power off until step 8 of bring-up.

## Soldering order

1. Female sockets for the 5 drivers. Fit a driver loosely while soldering so the two rows stay parallel.
2. Resistors, then ceramic capacitors.
3. Electrolytic capacitors C20-C24. The long leg (+) goes in the hole marked + in the wire list.
4. Plugs and screw terminals.
5. Work down `wire_list.csv`, ticking off each line. 24 V and ground are first and use 18 AWG.
6. Check with a meter before fitting any driver. See bring-up.

## Off-board wiring

### Power

| From | To | Wire |
|---|---|---|
| 24 V supply + | F0 (10 A), then K1 pin 30 | 18 AWG |
| F0 output | E-stop SW1, either terminal | 22 AWG |
| SW1 other terminal | K1 pin 85 | 22 AWG |
| K1 pin 86 | Ground | 22 AWG |
| D1 band (cathode) | K1 pin 85 | Solder at the relay socket |
| D1 other end | K1 pin 86 | Solder at the relay socket |
| K1 pin 87 | Carrier `24 V IN +` | 18 AWG |
| 24 V supply - | Carrier `24 V IN -` | 18 AWG |

The diode must have its band towards pin 85. Backwards, it shorts the relay coil.

### Gripper power

| From | To | Wire |
|---|---|---|
| Carrier `TO F1` | F1 (2 A), then U6 IN+ | 18 AWG |
| Carrier `TO U6` | U6 IN- | 18 AWG |
| U6 OUT+ | F2 (3 A), then tool plug pin 2 | 18 AWG |
| U6 OUT- | Tool plug pin 3 | 18 AWG |

Solder C7 (1000 uF, stripe to ground) and C8 (100 nF) across the 6 V output after F2.

**Set U6 to 6.0 V with a meter before connecting the servo.**

### Motors

Each motor plugs in beside its driver, from top to bottom: A2, A1, B1, B2.

| Plug pins | Motor coil |
|---|---|
| A2 and A1 | Coil A |
| B1 and B2 | Coil B |

Find each coil with a meter: the two wires of one coil read a few ohms between them, and wires from different coils read open. Do not trust wire colours. If a joint runs backwards, flip its `DIR_SIGN` in the firmware.

| Plug | Motor | Joint |
|---|---|---|
| M1 | 17HS19-1684S-PG5 | J1 base |
| M2 | 17HS19-1684S-PG14 | J2 shoulder |
| M3 | 17HS19-1684S-PG5 | J3 elbow |
| M4 | 17HS08-1004S | J4 wrist |
| M5 | 11HS12-0674S | J5 wrist twist |

### Encoders

Each AS5600 needs 5 wires from its plug and module.

| Carrier plug | AS5600 pin |
|---|---|
| OUT, top | OUT |
| 5V, middle | VCC, and also GPO |
| GND, bottom | GND, and also DIR |

Jumper GPO to VCC and DIR to GND on the module itself, so only 3 wires run up the arm. Leave SDA and SCL unconnected.

| Plug | Joint |
|---|---|
| E1 | J1 |
| E2 | J2 |
| E3 | J3 |
| E4 | J4 |
| E5 | J5 |

### Tool plug (GX12, at the wrist)

| Pin | Signal | Comes from |
|---|---|---|
| 1 | Servo PWM | Carrier `PWM` |
| 2 | 6 V | F2 |
| 3 | Ground | U6 OUT- |
| 4 | 5 V | Mega 5V |
| 5 | I2C SDA | Mega D20 |
| 6 | I2C SCL | Mega D21 |

Pins 4-6 are for future tools. The two-jaw gripper uses pins 1-3.

### Other

| From | To |
|---|---|
| Carrier `FAN` + and - | 40 mm fan. Check its polarity |
| Pi USB-A | Mega USB-B |
| Pi USB-C | Official Pi supply |

## Bring-up

Stop at the first thing that is wrong.

1. No drivers fitted. With everything unpowered, meter `24 V IN +` to `-`, and Mega 5V to GND. Neither should read a short.
2. Meter each driver socket: VM to ground, and VIO to ground. Neither should read a short, and VM and VIO must not be connected to each other.
3. Connect the Mega by USB only. Check 5 V on every socket's VIO pin.
4. Check each EN pin reads 5 V, which holds the drivers off.
5. Connect 24 V with the current limit at 0.5 A if your supply has one, and no drivers fitted. Press the E-stop and confirm 24 V at the carrier disappears. Release it and confirm it returns.
6. Check 24 V on all 5 VM pins. Set the buck to 6.0 V.
7. Power everything off. Fit one driver with **EN top-left**, and no motor.
8. Power on and check the firmware reports that driver over UART. Repeat for each driver, powering off each time.
9. Connect one motor with power off, and limit the supply to 3 A. Test one joint at low speed. Add the rest one at a time.

Never plug or unplug a motor with 24 V on. It can destroy the driver.

## Safety

- The 24 V supply and the Pi supply stay separate, but all grounds are common.
- Never connect 24 V or 6 V to any Mega pin.
- The E-stop cuts the motor bus only. The arm has no brakes, so it can fall.
