//@version=5
indicator("Minervini Pattern Detector PRO v3", shorttitle="MM_Patterns", overlay=true, max_labels_count=50)

// ══════════════════════════════════════════════════════════════════
// MINERVINI INSIGHT: VCP is a CHARACTERISTIC, not a separate pattern
// VCP appears in: Cup&Handle, Double Bottom, High Tight Flag, etc.
// ══════════════════════════════════════════════════════════════════

// ==========================
// INPUT
// ==========================
baseLen       = input.int(30, "Base Length (bars)", minval=15, maxval=100)
atrLen        = input.int(14, "ATR Length")
vcpSegLen     = input.int(7,  "T-Segment Length", tooltip="For T1/T2/T3 contraction")
pivotLook     = input.int(5,  "Pivot Lookback")

// Pattern-specific inputs
htfMinGain    = input.float(80.0, "HTF: Min Prior Gain %", tooltip="High Tight Flag: 100%+ gain in 8 weeks")
cupMinLen     = input.int(20, "Cup: Min Length", tooltip="Cup with Handle minimum bars")

// ==========================
// CORE METRICS
// ==========================
baseHigh = ta.highest(high, baseLen)
baseLow  = ta.lowest(low, baseLen)
baseDepthPct = (baseHigh - baseLow) / baseHigh * 100
pricePosPct  = (close - baseLow) / (baseHigh - baseLow) * 100
pivotDist    = (baseHigh - close) / baseHigh * 100

// Prior trend (need uptrend before base)
priorHigh = ta.highest(high[baseLen], baseLen)
priorLow  = ta.lowest(low[baseLen], baseLen)
priorGain = (baseHigh - priorLow) / priorLow * 100

// ==========================
// VCP CHARACTERISTIC (T-Count)
// ==========================
atrPct = ta.atr(atrLen) / close * 100

atr_T1 = ta.sma(atrPct, vcpSegLen * 4)
atr_T2 = ta.sma(atrPct, vcpSegLen * 3)
atr_T3 = ta.sma(atrPct, vcpSegLen * 2)
atr_T4 = ta.sma(atrPct, vcpSegLen)

// Count contractions (T's)
t1 = atr_T1 > atr_T2
t2 = atr_T2 > atr_T3
t3 = atr_T3 > atr_T4
tCount = (t1 ? 1 : 0) + (t2 ? 1 : 0) + (t3 ? 1 : 0)

hasVCPchar = tCount >= 2  // VCP characteristic present

// ==========================
// VOLUME ANALYSIS
// ==========================
upVol   = close > close[1] ? volume : 0
downVol = close < close[1] ? volume : 0
upVolMA   = ta.sma(upVol, 10)
downVolMA = ta.sma(downVol, 10)

volMA20 = ta.sma(volume, 20)
volMA50 = ta.sma(volume, 50)
volDryUp = volMA20 < volMA50 * 0.8
accumRatio = upVolMA / math.max(downVolMA, 1)
volHealthy = upVolMA >= downVolMA

// ==========================
// TIGHT ACTION
// ==========================
rangePct = (high - low) / close * 100
rangeMA5 = ta.sma(rangePct, 5)
rangeMA20 = ta.sma(rangePct, 20)
tightnessRatio = rangeMA5 / rangeMA20
higherLows = ta.lowest(low, pivotLook) >= ta.lowest(low, pivotLook * 2)
isTight = tightnessRatio < 0.9 and higherLows

// ==========================
// PATTERN DETECTION
// ==========================

// --- 1. HIGH TIGHT FLAG (HTF) ---
// 80-120%+ gain in 4-8 weeks, then tight 10-25% consolidation
htfPriorGain = priorGain >= htfMinGain
htfShallowBase = baseDepthPct <= 25 and baseDepthPct >= 10
htfTight = tightnessRatio < 0.6
isHTF = htfPriorGain and htfShallowBase and htfTight and pricePosPct >= 70

// --- 2. CUP WITH HANDLE ---
// U-shaped base (30-65% depth allowed), handle is smaller pullback
// Price should be in upper 1/3 for handle formation
cupDepthOK = baseDepthPct >= 15 and baseDepthPct <= 65
cupRounded = true  // Simplified: would need more complex detection
cupHandle = pricePosPct >= 70 and tightnessRatio < 0.85
isCup = cupDepthOK and cupHandle and tCount >= 1 and volDryUp

// --- 3. DOUBLE BOTTOM (W-Pattern) ---
// Two lows with middle peak, second low undercuts slightly
low1 = ta.lowest(low, baseLen / 2)
low2 = ta.lowest(low[baseLen/2], baseLen / 2)
middleHigh = ta.highest(high[baseLen/4], baseLen / 2)
hasWShape = math.abs(low1 - low2) / low1 * 100 < 5  // Two lows within 5%
isDoubleBottom = hasWShape and baseDepthPct >= 15 and baseDepthPct <= 50 and pricePosPct >= 60 and hasVCPchar

// --- 4. FLAT BASE ---
// Very shallow consolidation (≤15%), price holding near highs
isFlatBase = baseDepthPct <= 15 and pricePosPct >= 80 and volHealthy

// --- 5. ASCENDING BASE ---
// Series of higher lows, upward sloping support
pivotLow1 = ta.lowest(low, pivotLook)
pivotLow2 = ta.lowest(low[pivotLook], pivotLook)
pivotLow3 = ta.lowest(low[pivotLook*2], pivotLook)
ascendingSupport = pivotLow1 > pivotLow2 and pivotLow2 > pivotLow3
isAscending = ascendingSupport and baseDepthPct <= 35 and pricePosPct >= 50

// --- 6. POWER PLAY / 3C (Cup Completion Cheat) ---
// Early entry: price breaks out before full pattern completes
// Near pivot with extreme tightness
isPowerPlay = pivotDist <= 3 and tightnessRatio < 0.5 and volDryUp and hasVCPchar

// --- 7. CLASSIC VCP ---
// Standard volatility contraction with 2-4 T's
isVCP = hasVCPchar and baseDepthPct <= 35 and pricePosPct >= 60 and isTight and volDryUp

// ==========================
// PATTERN PRIORITY & SCORING
// ==========================
// Priority: Power Play > HTF > VCP > Cup > Double Bottom > Flat > Ascending > Forming > No Pattern

string patternName = "NO PATTERN"
int patternScore = 0
color patternColor = color.gray
string patternNote = ""

if isPowerPlay
    patternName := "POWER PLAY"
    patternScore := 95
    patternColor := color.fuchsia
    patternNote := "Early breakout entry!"
else if isHTF
    patternName := "HIGH TIGHT FLAG"
    patternScore := 90
    patternColor := color.lime
    patternNote := "Monster move ahead!"
else if isVCP
    patternName := "VCP (" + str.tostring(tCount) + "T)"
    patternScore := 85
    patternColor := color.lime
    patternNote := "Classic Minervini setup"
else if isCup
    patternName := "CUP & HANDLE"
    patternScore := 80
    patternColor := color.green
    patternNote := "Handle forming, wait pivot"
else if isDoubleBottom
    patternName := "DOUBLE BOTTOM"
    patternScore := 75
    patternColor := color.green
    patternNote := "W-pattern confirmed"
else if isFlatBase
    patternName := "FLAT BASE"
    patternScore := 70
    patternColor := color.teal
    patternNote := "Consolidating at highs"
else if isAscending
    patternName := "ASCENDING BASE"
    patternScore := 65
    patternColor := color.blue
    patternNote := "Support rising steadily"
else if hasVCPchar and pricePosPct >= 50
    patternName := "FORMING..."
    patternScore := 40
    patternColor := color.yellow
    patternNote := "Base building, not ready"
else if pricePosPct < 50
    patternName := "WEAK POSITION"
    patternScore := 20
    patternColor := color.orange
    patternNote := "Price in lower half of range"
else if baseDepthPct > 50
    patternName := "TOO DEEP"
    patternScore := 15
    patternColor := color.red
    patternNote := "Correction >50% = damaged"
else if not volHealthy
    patternName := "DISTRIBUTION"
    patternScore := 10
    patternColor := color.red
    patternNote := "Selling > Buying, avoid!"
else
    patternName := "NO SETUP"
    patternScore := 0
    patternColor := color.gray
    patternNote := "Wait for base to form"

// Component scores for breakdown
baseScore = baseDepthPct <= 15 ? 25 : baseDepthPct <= 25 ? 20 : baseDepthPct <= 35 ? 15 : baseDepthPct <= 50 ? 10 : 5
vcpScore = tCount >= 3 ? 25 : tCount >= 2 ? 20 : tCount >= 1 ? 10 : 0
volScore = (volHealthy ? 10 : 0) + (volDryUp ? 10 : 0) + (accumRatio >= 1.5 ? 5 : 0)
tightScore = (tightnessRatio < 0.7 ? 15 : tightnessRatio < 0.9 ? 10 : 5) + (higherLows ? 10 : 0)
totalScore = baseScore + vcpScore + volScore + tightScore

// Grade
string grade = patternScore >= 85 ? "A+" : patternScore >= 70 ? "A" : patternScore >= 50 ? "B" : patternScore >= 30 ? "C" : "F"

// ==========================
// LABEL DISPLAY
// ==========================
var label lbl = na

if barstate.islast
    if not na(lbl)
        label.delete(lbl)

    string lblText = 
         "【" + patternName + "】\n" +
         patternNote + "\n" +
         "Grade: " + grade + " | Score: " + str.tostring(patternScore) + "\n" +
         "═══════════════════\n" +
         "① Base: " + str.tostring(baseScore) + "/25\n" +
         "   Depth:" + str.tostring(baseDepthPct, "#.#") + "% Pos:" + str.tostring(pricePosPct, "#.#") + "%\n" +
         "   Pivot dist: " + str.tostring(pivotDist, "#.#") + "%\n" +
         "② VCP: " + str.tostring(vcpScore) + "/25\n" +
         "   T-Count: " + str.tostring(tCount) + " (T1:" + (t1?"Y":"N") + " T2:" + (t2?"Y":"N") + " T3:" + (t3?"Y":"N") + ")\n" +
         "③ Volume: " + str.tostring(volScore) + "/25\n" +
         "   Accum:" + str.tostring(accumRatio, "#.##") + "x DryUp:" + (volDryUp ? "Y" : "N") + "\n" +
         "④ Tight: " + str.tostring(tightScore) + "/25\n" +
         "   Ratio:" + str.tostring(tightnessRatio, "#.##") + " HL:" + (higherLows ? "Y" : "N") + "\n" +
         "═══════════════════\n" +
         "Prior Gain: " + str.tostring(priorGain, "#.#") + "%"

    lbl := label.new(bar_index + 5, close, lblText, 
         xloc=xloc.bar_index, yloc=yloc.price, 
         color=patternColor, style=label.style_label_right, 
         textcolor=color.white, size=size.small)

// ==========================
// VISUAL AIDS
// ==========================
color bgCol = patternScore >= 85 ? color.new(color.lime, 92) : patternScore >= 70 ? color.new(color.green, 94) : patternScore >= 50 ? color.new(color.yellow, 95) : na
bgcolor(bgCol)

plot(baseHigh, "Pivot", color=color.new(color.aqua, 60), style=plot.style_circles)

// Alert conditions
alertcondition(isPowerPlay, "Power Play Detected", "Power Play setup!")
alertcondition(isHTF, "High Tight Flag", "HTF pattern detected!")
alertcondition(isVCP and tCount >= 2, "VCP Ready", "VCP pattern  detected with contractions!")

