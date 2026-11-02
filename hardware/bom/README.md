# Bill of materials

Complete build list for the arm in [docs/mechanical-design.md](../../docs/mechanical-design.md). Machine-readable version with pack sizes and notes: [bom.csv](bom.csv).

| Phase | Cost |
|---|---|
| Phase 1: base, J1, gripper and electronics test | $325 |
| Phase 2: the rest of the electronics and motors | $103 |
| Phase 3: mechanical for the arm | $112 |
| **Total, before tax and shipping** | **about $540** |

Totals leave out parts already owned (marked Owned, about $321). Confirm the Raspberry Pi is a Pi 5 and that the 24 V supply can deliver 5 A.

**Price status:** `checked` was read from Amazon on 2 November 2026. `estimate` is the October 2026 figure. `rough` is an unconfirmed planning number with no link yet; find the listing by part number. Only $42 of the total is `checked`, so check the cart before ordering.

## Check before ordering

- **K1:** confirm the relay coil is 24 V. Many similar automotive relays are 12 V.
- **AS5600:** confirm the modules run at 5 V, include diametric magnets, and that analog OUT is not disabled by a resistor on GPO. Test one first.
- **TMC2209:** confirm the UART pin and whether the module needs a solder bridge. Test one first.
- **Capacitors:** confirm the kit contains 100 uF 35 V and 1000 uF 16 V.
- **17HS19-1684S-PG5:** confirm the 8 mm output shaft and gearbox bolt pattern, then match `motor_plate` in `hardware/mechanical/cad/base_j1.py`.
- **17HS19-1684S-PG14:** confirm the gearbox permissible torque is at least 3 N·m.

## Phase 1: base, J1, gripper and electronics test (buy now)

| Ref | Part | Need | Buy | Est. | Price |
|---|---|---|---|---|---|
| U2 | Arduino Mega 2560 R3 (or compatible) | 1 | Owned | $22.00 | rough |
| PS1 | 24 V bench supply with adjustable current limit, 5 A or more | 1 | Owned | $70.00 | rough |
| DRV1-5 | [BIGTREETECH TMC2209 V1.3, 5-pack with heatsinks](https://www.amazon.com/BIGTREETECH-DIRECT-TMC2209-Stepsticks-Motherboard/dp/B07ZQ3C1XW) | 5 | 1 x 5-pack | $33.00 | estimate |
| M1 | STEPPERONLINE 17HS19-1684S-PG5 NEMA 17, 5.18:1 planetary (J1) | 1 | 1 | $32.00 | rough |
| ENC1-5 | [AS5600 encoder modules, 10-pack](https://www.amazon.com/AS5600-Magnetic-Encoder-Induction-Measurement/dp/B0D3WMK5MT) | 5 | 1 x 10-pack | $15.00 | estimate |
| SW1 | [E-stop, 22 mm latching mushroom, 1 NC](https://www.amazon.com/COMOK-Emergency-Self-Locking-Push-Button-ZB2-BE102C/dp/B07MJPRMRL) | 1 | 1 | $9.99 | checked |
| K1 | [24 V 30 A relay, normally open, wired socket](https://www.amazon.com/Normally-Automotive-Relay-18AWG-Socket/dp/B0CQFG7WZV) | 1 | 1 | $8.00 | estimate |
| D1 (new) | 1N4007 diode pack, flyback across K1 coil | 1 | 1 x 20-pack | $6.00 | rough |
| F0 | [Inline ATO fuse holders with 5-30 A fuses, 5-pack](https://www.amazon.com/Inline-Holder-Blade-3-2Ft-Electric/dp/B0B4JTWJDT) | 3 | 1 x 5-pack | $12.00 | estimate |
| F1-F2 | ATO fuses, low-amp assortment including 2 A and 3 A | 2 | 1 x 10-pack | $8.00 | rough |
| C7,C20-25 | [Electrolytics: 1000 uF 16 V x1, 100 uF 35 V x6](https://www.amazon.com/OQATNXUR-Electrolytic-Capacitor-Assortment-1000uf/dp/B0DDCB76H9) | 7 | 1 | $12.00 | estimate |
| C1-6,C8 | [Ceramic capacitor kit including 100 nF](https://www.amazon.com/BOJACK-Ceramic-Capacitor-Assortment-Capacitors/dp/B07P8N8BW9) | 7 | 1 | $10.00 | estimate |
| R1-6,R13,R21-26,R31-32 | [Metal film resistor kit: 1k x9, 10k x6](https://www.amazon.com/Elegoo-Values-Resistor-Assortment-Compliant/dp/B072BL2VX1) | 15 | 1 x 525-pack | $10.00 | estimate |
| - | [ElectroCookie prototype boards, 3-pack](https://www.amazon.com/Prototype-Solderable-Breadboard-Electronics-Gold-Plated/dp/B082KY5Y5Z) | 1 | 1 x 3-pack | $12.00 | estimate |
| - | [2.54 mm female headers (driver sockets)](https://www.amazon.com/Glarks-Straight-Connector-Assortment-Prototype/dp/B076GZXW3Z) | 1 | 1 | $8.00 | estimate |
| FAN1 | [40 mm 5 V fan, 2-pack](https://www.amazon.com/WINSINN-Bearings-Brushless-Cooling-40mm10mm/dp/B08R9JJDYP) | 1 | 1 x 2-pack | $9.00 | estimate |
| - | [USB-A to USB-B cable](https://www.amazon.com/amazonbasics-usb-2-0-cable-male/dp/b00nh11kik) | 1 | Owned | $5.00 | estimate |
| - | [18 AWG silicone wire kit (24 V, motors)](https://www.amazon.com/CBAZY-Stranded-Flexible-Silicone-Electric/dp/B073RDBW7L) | 1 | Owned | $15.00 | estimate |
| - | [22 AWG silicone wire kit (signals)](https://www.amazon.com/CBAZY-Flexible-Silicone-Stranded-Electric/dp/B073RF4YY4) | 1 | Owned | $13.00 | estimate |
| J1 | 6813-2RS thin bearing, 65x85x10 mm | 2 | 2 | $20.00 | rough |
| J1 | GT2 closed belt, 360 mm long, 15 mm wide (360-2GT-15) | 1 | 1 | $10.00 | rough |
| J1 | GT2 20-tooth pulley, 8 mm bore, for 15 mm belt | 1 | 1 | $8.00 | rough |
| - | M3/M4/M5 screw, nut and washer assortment | 1 | 1 | $30.00 | rough |
| - | M3/M4 brass heat-set inserts | 1 | 1 | $12.00 | rough |
| Base | C-clamps or table bolts, set of 2 | 1 | 1 x 2-pack | $12.00 | rough |
| - | PETG filament, 1 kg rolls | 2 | Owned | $40.00 | rough |
| M7 | [MG996R servo, 4-pack (J6 gripper)](https://www.amazon.com/MG996R-Copper-Digital-Helicopter-Control/dp/B0DK1V5ZSM) | 1 | 1 x 4-pack | $22.99 | checked |
| U6 | [XL4015 5 A buck module, 3-pack (set to 6.0 V)](https://www.amazon.com/HiLetgo-1-25-36V-Converter-Adjustable-Step-down/dp/B00LOG4XC0) | 1 | 1 x 3-pack | $9.49 | checked |
| Gripper | TPU filament or rubber pads for jaws | 1 | 1 | $10.00 | rough |
| Gripper | 4 mm steel rod, 110 mm (gripper guides) | 2 | 1 x 2-pack | $6.00 | rough |
| | **Subtotal to buy** | | | **$325.47** | |

## Phase 2: the rest of the electronics and motors (buy after J1 works)

| Ref | Part | Need | Buy | Est. | Price |
|---|---|---|---|---|---|
| M2 | STEPPERONLINE 17HS19-1684S-PG14 NEMA 17, 13.73:1 planetary (J2) | 1 | 1 | $35.00 | rough |
| M3 | STEPPERONLINE 17HS19-1684S-PG5 NEMA 17, 5.18:1 planetary (J3) | 1 | 1 | $32.00 | rough |
| M4 | [STEPPERONLINE 17HS08-1004S short NEMA 17, 16 N·cm (J4)](https://www.amazon.com/STEPPERONLINE-Bipolar-Stepper-22-6oz-Extruder/dp/B00PNEQ79Q) | 1 | 1 | $11.00 | estimate |
| M5 | STEPPERONLINE 11HS20-0674S NEMA 11, 12 N·cm (J5 wrist twist) | 1 | 1 | $15.00 | rough |
| U1 | Raspberry Pi 5 8 GB | 1 | Owned | $95.00 | rough |
| PS2 | Official Raspberry Pi 27 W USB-C supply | 1 | Owned | $12.00 | rough |
| - | Raspberry Pi 5 Active Cooler | 1 | Owned | $10.00 | rough |
| - | microSD card, 64 GB (Ubuntu 24.04, ROS 2) | 1 | Owned | $12.00 | rough |
| - | JST-XH connector kit with crimper-free pre-crimped leads | 1 | Owned | $15.00 | rough |
| J6 | GX12 6-pin connector pair (tool plug at the wrist) | 1 | 1 | $10.00 | rough |
| - | Heat shrink and braided sleeve | 1 | Owned | $12.00 | rough |
| | **Subtotal to buy** | | | **$103.00** | |

## Phase 3: mechanical for the arm (buy after CAD is frozen)

| Ref | Part | Need | Buy | Est. | Price |
|---|---|---|---|---|---|
| J5 | 6803 bearing, 17x26x5 mm | 2 | 2 | $6.00 | rough |
| J2 | 6806 thin bearing, 30x42x7 mm | 2 | 2 | $8.00 | rough |
| J3 | 6804 thin bearing, 20x32x7 mm | 2 | 2 | $8.00 | rough |
| J4 | 6802 bearing, 15x24x5 mm | 2 | 2 | $6.00 | rough |
| J2 | GT2 closed belt, 280 mm long, 15 mm wide (280-2GT-15) | 1 | 1 | $10.00 | rough |
| J3 | GT2 closed belt, 380 mm long, 15 mm wide (380-2GT-15) | 1 | 1 | $10.00 | rough |
| J4-J5 | GT2 closed belts, 6 mm wide, lengths from CAD | 3 | 3 | $12.00 | rough |
| J2 | GT2 20-tooth pulley, 8 mm bore, for 15 mm belt | 1 | 1 | $8.00 | rough |
| J3 | GT2 16-tooth pulley, 8 mm bore, for 15 mm belt | 1 | 1 | $8.00 | rough |
| J3 | GT2 idler for 15 mm belt | 1 | 1 | $2.00 | rough |
| J4 | GT2 small pulleys, 5 mm bore, 20T and 16T, for 6 mm belt | 2 | 2 | $7.00 | rough |
| J4 | GT2 idler for 6 mm belt | 1 | 1 | $2.00 | rough |
| J5 | GT2 16-tooth pulley, 5 mm bore, for 6 mm belt | 1 | 1 | $3.00 | rough |
| J2 | Extension springs for counterbalance, assortment | 1 | 1 | $12.00 | rough |
| Forearm | 10 mm aluminium rod, 200 mm | 2 | 1 x 2-pack | $10.00 | rough |
| | **Subtotal to buy** | | | **$112.00** | |

Tools are not included: soldering iron, multimeter, 3D printer with a bed of at least 220 mm, hex keys.
