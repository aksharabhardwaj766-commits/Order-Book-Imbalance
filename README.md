# Order Book Imbalance
Order Book Imbalance (OBI) measures buy v/s sell pressure in order book, using `bid volume - ask volume/ bid volume + ask volume`, to test whether it predicts short term price moves.

## Why it matters ?

OBI asks: is there more buying or selling pressure sitting in the book right now ?

If there's more volume stacked on the bid side than the ask side. That imbalance is a signal that price is more likely to tick up next -- because there are more buyers waiting than sellers,
so it takes less selling pressure to eat through the ask side than it would take buying pressure to eat through the bid side.

## Data Used 

- LOBSTER sample data of AAPL, MSFT

## Results/Observations 

- Depth 1 OBI signal is statistically real, not luck -- it survives a strict correlation for testing 12 things at once.
- Depth 5 significant at all 4 horizons: but negative correlation (weaker economic signal despite statistical significance)
- Depth 10: significant unto 30s; breaks down at 100s -- significance disappear at longest horizons.

## For depth5/10 correlation is negative but still significance = True. why?

- Because of sample size (n ~ 395,651 rows) is huge.
- significance depends on two things: 1) How strong the correlation is ? 2) How many data points we have ?
- With a massive n, even a tiny correlation like -0.016 for depth5 x 1s becomes statistically significant.
- This correlation is **basically zero in practical terms**, but with ~395K rows, even -0.016 is reliably not zero.

## Pipeline
### Forward Return Labelling (`data_labels.py`)
- For each row compute what happens to mid_price a few ticks/seconds later.
- Data is event driven = rows arrive irregularly (sometimes 3 events in 1ms, sometimes nothing for 2sec)

### Correlation Test (`main.ipynb`)
- Spearman correlation is used (uses rank, not abs values, therefore less impact of outliers)
- 3 depth x 4 horizons = 12 pairs (Results live in a DataFrame)

### Plot

- Line plot of OBI vs forward returns.
- *Observation:* Correlation strength decays as the horizon decreases. 

### Pre-Registered Significance Test + Bonferroni Correlation (`main.ipynb`)
- Bonferroni Correlation: adjusts the significance threshold when running many tests at once, so that we don't get a false positive
- **Why needed ?**
  - With alpha = 0.5, each test has a 5% chance of a false positive.
  - **Fix**: New threshold = alpha/no. of tests (in this case = 0.5/12 = 0.00417)
  - **Use**: We will call a test significant if p-value < 0.00417
                                                else NOT
## Cross Ticker Robustness
### MSFT Cross Ticker comparison: AAPL vs MSFT
- Investigated whether book depth explains - MSFT has stronger OBI-Correlation returns than AAPL.
  Depth was ruled out because in both share-count and dollar depth, MSFT is actually deeper than AAPL, which rules out thinner book theory.

- Actual driver was **relative tick size**: MSFT trades at ~$30, while AAPL at ~$580. This means $0.01 tick is ~19x larger than MSFT's price.
  This makes MSFT's price grid coarser -- AAPL's best ask changes 32,999 times in a day (with 1,062 unique prices) while MSFT's change 3,258 times (with 109 uniqu prices) 
  and MSFT also shows multi-minute quiet stretches (82 gaps 60 seconds, max gap - 207 seconds), these never occur in AAPL.

- A coarser, stickier price grid gives more order flow more time to build at a given level before price move, which lets obi reflect real buy/sell pressure, ahead of the move.

- Confirmed this is a genuine market microstructure effect and not a labelling artifact: forward returns (`data_labels.py`) are computed in calander time via merge_asof, 
  so the horizon means the same real world time gap for both stocks despite different row counts.


## File Structure
```
|-`lobster_loader.py` - loads LOBSTER data
|-`data_labels.py` - adds forward returns (calendar-time, via merge_asof)
|-`obi.py` - Computes OBI at depths 1/5/10
|-`main.ipynb` - AAPL: correlation test, Bonferroni, Plots
|-`main_MSFT.ipynb` - MSFT: correlation test, Bonferroni, Plots
```

## Requirenments

pandas

numpy

matplotlib

scipy

scikit-learn

pytest
