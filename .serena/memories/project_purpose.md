# Project Purpose

`pi0disp` is a high-speed Python display driver library designed for Raspberry Pi (especially resource-constrained models like Pi Zero 2W) to efficiently drive ST7789V-based displays. It leverages `pigpio` for SPI communication and incorporates advanced optimization techniques such as:
- Dirty region updates (only updating changed screen areas)
- Memory pooling
- Adaptive data transfer chunk size adjustment

These optimizations aim to achieve high frame rates with low CPU overhead. The project also provides a simple CLI tool for basic operational checks and performance measurements.