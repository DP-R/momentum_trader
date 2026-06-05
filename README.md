# Momentum Trading Project

This project implements a momentum trading strategy using Python. It extracts historical stock data, calculates various technical indicators, screens stocks based on specific criteria, and generates trade plans.

## Project Structure

```
momentum_trader_project
├── notebooks
│   └── momentum_trader.ipynb        # Jupyter notebook with the original momentum trading strategy code
├── src
│   ├── __init__.py                   # Marks the src directory as a Python package
│   ├── config.py                     # Configuration constants for the project
│   ├── data_extractor.py             # Functions for extracting historical stock data
│   ├── indicators.py                  # Functions for calculating technical indicators
│   ├── screening.py                   # Functions for screening stocks based on criteria
│   └── trade_plan.py                  # Functions for generating trade plans
├── tests
│   ├── test_data_extractor.py        # Unit tests for data extraction functions
│   ├── test_indicators.py             # Unit tests for technical indicator calculations
│   ├── test_screening.py              # Unit tests for stock screening logic
│   └── test_trade_plan.py             # Unit tests for trade plan generation
├── pyproject.toml                     # Configuration file for the project
├── requirements.txt                   # List of required Python packages
└── README.md                          # Documentation for the project
```

## Installation

To set up the project, clone the repository and install the required packages:

```bash
git clone <repository-url>
cd momentum_trader_project
pip install -r requirements.txt
```

## Usage

1. **Data Extraction**: Use the functions in `data_extractor.py` to fetch historical stock data from Yahoo Finance.
2. **Indicator Calculation**: Utilize the functions in `indicators.py` to compute technical indicators such as ATR, ADX, and RSI.
3. **Stock Screening**: Apply the screening functions in `screening.py` to filter stocks based on liquidity and volatility.
4. **Trade Planning**: Generate trade plans using the functions in `trade_plan.py`, which will provide entry points, stop losses, and target prices.

## Testing

Unit tests are provided for each module in the `tests` directory. To run the tests, use:

```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.