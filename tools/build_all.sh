#!/bin/bash

./generate_table.py -x leg_spec.xml -l leg_lut.dat -i leg_interp.dat
./graph_lut.py -l leg_lut.dat -o envelope.png
