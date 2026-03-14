//@version=5
indicator("Minervini RS VNStock", shorttitle="RS_VN", overlay=false)

//----------------------------
// Inputs - VIETNAM STOCK VERSION
// Benchmark: VNINDEX for Vietnam market
//----------------------------
benchmarkSymbol = input.symbol("HOSE:VNINDEX", "Benchmark (VNINDEX)")
smoothLength    = input.int(10, "SMA của RS", minval=1, maxval=50)

//----------------------------
// RS raw (price / benchmark)
//----------------------------
benchClose = request.security(benchmarkSymbol, timeframe.period, close)
rsRaw      = benchClose != 0.0 ? close / benchClose : na

// Normalize 0 → 100
rsLookback = math.min(200, bar_index + 1)
rsHigh     = ta.highest(rsRaw, rsLookback)
rsLow      = ta.lowest(rsRaw, rsLookback)
rsRange    = rsHigh - rsLow
rsNorm     = rsRange != 0.0 ? 100.0 * (rsRaw - rsLow) / rsRange : na

// Smoothed RS
rsSmooth = ta.sma(rsNorm, smoothLength)

//----------------------------
// Plot
//----------------------------
plot(rsNorm,   "RS (0–100)", color=color.new(color.purple, 0), linewidth=2)
plot(rsSmooth, "RS SMA",     color=color.new(color.white, 0),  linewidth=1)

// Levels
hline(80, "RS 80 (Leader)", color=color.new(color.green, 70))
hline(70, "RS 70",          color=color.new(color.orange, 70))
hline(50, "RS 50",          color=color.new(color.gray, 70))
hline(20, "RS Weak",        color=color.new(color.red, 70))
