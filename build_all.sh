#!/bin/bash

./generate_table.py -x spec/leg_spec.xml -l lut/leg_lut.dat -i lut/leg_interp.dat
./graph_lut.py -l lut/leg_lut.dat -o envelope.png
