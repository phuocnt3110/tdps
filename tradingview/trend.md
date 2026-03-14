//@version=5
indicator("Minervini Score + 52W (No RS)", shorttitle="Minervini_Score", overlay=true, max_labels_count=500)

//------------------------
// Inputs
//------------------------
benchmarkSymbol = input.symbol("HOSE:VNINDEX", "Benchmark (RS)")
nearHighPct     = input.float(25.0, "Near 52W high threshold (%)", minval=1, maxval=50)
bars52          = input.int(252, "Bars ≈ 52 weeks", minval=50, maxval=400)

//------------------------
// Moving averages (price & volume)
//------------------------
ma_price20 = ta.sma(close, 20)
ma50  = ta.sma(close, 50)
ma150 = ta.sma(close, 150)
ma200 = ta.sma(close, 200)
volMa = ta.sma(volume, 20)

//------------------------
// Relative Strength raw (KHÔNG PLOT, chỉ để tính điểm)
//------------------------
benchClose = request.security(benchmarkSymbol, timeframe.period, close)
rsRaw      = benchClose != 0.0 ? close / benchClose : na

rsLookback = math.min(200, bar_index + 1)
rsHigh     = ta.highest(rsRaw, rsLookback)
rsLow      = ta.lowest(rsRaw, rsLookback)
rsRange    = rsHigh - rsLow
rsNorm     = rsRange != 0.0 ? 100.0 * (rsRaw - rsLow) / rsRange : na

//------------------------
// 52-week metrics
//------------------------
lookback52     = math.min(bars52, bar_index + 1)
hi52           = ta.highest(high, lookback52)
distFrom52High = hi52 != 0.0 ? (close - hi52) / hi52 * 100.0 : na
isNearHigh     = not na(distFrom52High) and distFrom52High >= -nearHighPct

price52Ago = bar_index > bars52 ? close[bars52] : na
perf52w    = not na(price52Ago) and price52Ago != 0.0 ?
     (close - price52Ago) / price52Ago * 100.0 : na

//------------------------
// Minervini conditions & score
//------------------------
condPriceAboveAll = close > ma50 and close > ma150 and close > ma200
condMaStacked     = ma50 > ma150 and ma150 > ma200
condMaSlope       = ma50 > ma50[5] and ma150 >= ma150[5] and ma200 >= ma200[5]
condRsUp          = rsNorm > rsNorm[5]
condVolStrong     = volume > volMa

score = 0
score += condPriceAboveAll ? 2 : 0
score += condMaStacked     ? 2 : 0
score += condMaSlope       ? 2 : 0
score += isNearHigh        ? 2 : 0
score += condRsUp          ? 1 : 0
score += condVolStrong     ? 1 : 0

isAPlus = score >= 8
isGood  = score >= 5 and score < 8

//------------------------
// Plot MA & Colors
//------------------------
plot(ma_price20,  "MA20",  color=color.new(color.white, 0),  linewidth=1)
plot(ma50,  "MA50",  color=color.new(color.green, 0),  linewidth=1)
plot(ma150, "MA150", color=color.new(color.orange, 0), linewidth=1)
plot(ma200, "MA200", color=color.new(color.red, 0),    linewidth=1)

color barCol = color.new(color.gray, 40)
barCol := isGood  ? color.new(color.orange, 0) : barCol
barCol := isAPlus ? color.new(color.lime, 0)   : barCol
barcolor(barCol)

//------------------------
// Label info on last bar
//------------------------
txt =
  "Score: " + str.tostring(score) + "/10\n" +
  "Near 52W High (<" + str.tostring(nearHighPct) + "%): " + (isNearHigh ? "YES" : "NO") + "\n" +
  "52W Perf: " + (na(perf52w) ? "n/a" : str.tostring(perf52w, "#.##") + "%") + "\n" +
  "Dist 52W High: " + (na(distFrom52High) ? "n/a" : str.tostring(distFrom52High, "#.##") + "%") + "\n" +
  "RS now: " + (na(rsNorm) ? "n/a" : str.tostring(rsNorm, "#.##"))

float yLbl = high * 1.05
var label lbl = na
if barstate.islast
    label.delete(lbl)
    lbl := label.new(
         bar_index, yLbl, txt,
         xloc = xloc.bar_index,
         yloc = yloc.price,
         style = label.style_label_left,
         textcolor = color.white,
         color = isAPlus ? color.new(color.green, 70) :
                 isGood  ? color.new(color.orange, 70) :
                           color.new(color.red, 80),
         size = size.small)
