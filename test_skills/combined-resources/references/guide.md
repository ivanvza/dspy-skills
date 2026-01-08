# Data Interpretation Guide

This guide explains how to interpret the data in `assets/data.csv`.

## Region Codes

| Code | Region Name | Description |
|------|-------------|-------------|
| R01 | North | Northern territories |
| R02 | South | Southern territories |
| R03 | East | Eastern territories |
| R04 | West | Western territories |
| R05 | Central | Central region |

## Status Codes

| Code | Meaning |
|------|---------|
| A | Active |
| I | Inactive |
| P | Pending |

## Data File Format

The CSV file contains the following columns:
1. `id` - Unique identifier
2. `region` - Region code (R01-R05)
3. `status` - Status code (A, I, P)
4. `value` - Numeric value

## How to Read the Data

1. Look up the region code in the Region Codes table
2. Look up the status code in the Status Codes table
3. The value column contains raw numeric data
