import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function WinRateThresholdCalculator() {
  const [gainRate, setGainRate] = useState(16);
  const [lossRate, setLossRate] = useState(8);
  const [cycles, setCycles] = useState(24);
  const [initial, setInitial] = useState(100000);

  const calculate = () => {
    const g = gainRate / 100;
    const l = lossRate / 100;
    
    // Tính ngưỡng win rate tối thiểu để không lỗ
    const minWinRate = Math.log(1/(1-l)) / (Math.log(1+g) + Math.log(1/(1-l)));
    
    // Tính cho các win rate khác nhau
    const data = [];
    const breakEvenPoints = [];
    
    for (let p = 0; p <= 100; p += 2) {
      const pDecimal = p / 100;
      
      // Geometric mean return
      const R = Math.pow(1+g, pDecimal) * Math.pow(1-l, 1-pDecimal);
      
      // Arithmetic mean return  
      const A = 1 + pDecimal * g - (1-pDecimal) * l;
      
      // Sau n chu kỳ
      const totalReinvest = Math.pow(R, cycles);
      const totalNoReinvest = 1 + cycles * (pDecimal * g - (1-pDecimal) * l);
      
      const finalReinvest = initial * totalReinvest;
      const finalNoReinvest = initial * totalNoReinvest;
      
      const advantage = ((R - A) * 100).toFixed(4);
      
      data.push({
        winRate: p,
        R: (R - 1) * 100,
        A: (A - 1) * 100,
        advantage: parseFloat(advantage),
        reinvest: Math.round(finalReinvest),
        noReinvest: Math.round(finalNoReinvest),
        diff: Math.round(finalReinvest - finalNoReinvest)
      });
      
      // Tìm điểm hòa vốn
      if (p > 0 && data.length > 1) {
        const prev = data[data.length - 2];
        const curr = data[data.length - 1];
        if (prev.diff < 0 && curr.diff >= 0) {
          breakEvenPoints.push({
            winRate: p,
            cycles: cycles
          });
        }
      }
    }
    
    // Tính ngưỡng cho các số chu kỳ khác nhau
    const cycleThresholds = [];
    for (let n = 10; n <= 100; n += 10) {
      let threshold = 0;
      for (let p = 0; p <= 100; p += 0.5) {
        const pDecimal = p / 100;
        const R = Math.pow(1+g, pDecimal) * Math.pow(1-l, 1-pDecimal);
        const A = 1 + pDecimal * g - (1-pDecimal) * l;
        
        const totalR = Math.pow(R, n);
        const totalA = 1 + n * (pDecimal * g - (1-pDecimal) * l);
        
        if (totalR >= totalA) {
          threshold = p;
          break;
        }
      }
      
      cycleThresholds.push({
        cycles: n,
        threshold: threshold.toFixed(1),
        epsilon: ((Math.pow(1+g, threshold/100) * Math.pow(1-l, 1-threshold/100) - 1) * 100).toFixed(2)
      });
    }
    
    return {
      data,
      minWinRate: minWinRate * 100,
      breakEvenPoints,
      cycleThresholds,
      g,
      l
    };
  };

  const result = calculate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2 text-center">
          Ngưỡng Win Rate để Tái đầu tư
        </h1>
        <p className="text-slate-400 text-center mb-8">
          Win rate cần bao nhiêu để lãi kép có lợi hơn?
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          {/* Input Panel */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <h2 className="text-xl font-semibold text-white mb-4">Tham số</h2>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-300 block mb-2">
                  Gain Rate: {gainRate}%
                </label>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={gainRate}
                  onChange={(e) => setGainRate(Number(e.target.value))}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <label className="text-sm text-slate-300 block mb-2">
                  Loss Rate: {lossRate}%
                </label>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={lossRate}
                  onChange={(e) => setLossRate(Number(e.target.value))}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <label className="text-sm text-slate-300 block mb-2">
                  Số chu kỳ: {cycles}
                </label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="2"
                  value={cycles}
                  onChange={(e) => setCycles(Number(e.target.value))}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <label className="text-sm text-slate-300 block mb-2">
                  Vốn ban đầu
                </label>
                <input
                  type="number"
                  value={initial}
                  onChange={(e) => setInitial(Number(e.target.value))}
                  className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Key Metrics */}
            <div className="mt-6 space-y-3">
              <div className="bg-red-500/20 backdrop-blur-lg rounded-xl p-4 border border-red-400/50">
                <div className="text-xs text-red-300 mb-1">Win rate tối thiểu (không lỗ)</div>
                <div className="text-2xl font-bold text-white">
                  ≥ {result.minWinRate.toFixed(1)}%
                </div>
              </div>

              {result.breakEvenPoints.length > 0 && (
                <div className="bg-yellow-500/20 backdrop-blur-lg rounded-xl p-4 border border-yellow-400/50">
                  <div className="text-xs text-yellow-300 mb-1">
                    Ngưỡng hòa với {cycles} chu kỳ
                  </div>
                  <div className="text-2xl font-bold text-white">
                    ≥ {result.breakEvenPoints[0].winRate}%
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Charts */}
          <div className="lg:col-span-3 space-y-6">
            {/* Advantage Chart */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-4">
                Lợi thế tái đầu tư (R - A) theo Win Rate
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={result.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="winRate" 
                    stroke="#94a3b8"
                    label={{ value: 'Win Rate (%)', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    label={{ value: 'Lợi thế (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                  />
                  <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="3 3" />
                  <Line 
                    type="monotone" 
                    dataKey="advantage" 
                    stroke="#10b981" 
                    strokeWidth={3}
                    dot={false}
                    name="R - A"
                  />
                </LineChart>
              </ResponsiveContainer>
              <p className="text-xs text-slate-400 mt-2">
                • Trên 0: Tái đầu tư có lợi | Dưới 0: Rút lời có lợi
              </p>
            </div>

            {/* Profit Comparison */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-4">
                So sánh lợi nhuận sau {cycles} chu kỳ
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={result.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="winRate" 
                    stroke="#94a3b8"
                    label={{ value: 'Win Rate (%)', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    tickFormatter={(value) => `${(value/1000).toFixed(0)}k`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                    formatter={(value) => `${value.toLocaleString('vi-VN')} đ`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="reinvest" 
                    stroke="#a855f7" 
                    strokeWidth={2}
                    name="Tái đầu tư"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="noReinvest" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    name="Không tái đầu tư"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Threshold Table */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
          <h3 className="text-lg font-semibold text-white mb-4">
            Ngưỡng Win Rate theo số chu kỳ (g={gainRate}%, l={lossRate}%)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-slate-300">Số chu kỳ</th>
                  <th className="text-left py-3 px-4 text-slate-300">Win rate tối thiểu</th>
                  <th className="text-left py-3 px-4 text-slate-300">R tối thiểu</th>
                  <th className="text-left py-3 px-4 text-slate-300">Ý nghĩa</th>
                </tr>
              </thead>
              <tbody className="text-white">
                {result.cycleThresholds.map((row, idx) => (
                  <tr key={idx} className="border-b border-slate-800 hover:bg-white/5">
                    <td className="py-3 px-4">{row.cycles}</td>
                    <td className="py-3 px-4 font-semibold">
                      ≥ {row.threshold}%
                    </td>
                    <td className="py-3 px-4">
                      1 + {row.epsilon}%
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-400">
                      {parseFloat(row.threshold) < 40 
                        ? 'Rất dễ đạt - Ưu tiên tái đầu tư' 
                        : parseFloat(row.threshold) < 50 
                        ? 'Khả thi - Cân nhắc tái đầu tư'
                        : 'Khó đạt - Nên rút lời'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Formula */}
        <div className="mt-6 bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
          <h3 className="text-lg font-semibold text-white mb-3">Công thức tổng quát</h3>
          <div className="text-slate-300 space-y-3 text-sm">
            <div className="bg-slate-800/50 p-4 rounded-lg font-mono">
              <div className="text-green-400 mb-2">Nên tái đầu tư khi:</div>
              <div>(1+g)^p × (1-l)^(1-p) &gt; 1 + p×g - (1-p)×l</div>
            </div>
            
            <div className="bg-slate-800/50 p-4 rounded-lg font-mono">
              <div className="text-yellow-400 mb-2">Win rate tối thiểu để không lỗ:</div>
              <div>p ≥ ln(1/(1-l)) / [ln(1+g) + ln(1/(1-l))]</div>
              <div className="text-xs text-slate-400 mt-2">
                Với g={gainRate}%, l={lossRate}% → p ≥ {result.minWinRate.toFixed(1)}%
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="bg-red-900/30 p-3 rounded border border-red-600/50">
                <strong className="text-red-300">Win rate thấp (&lt;40%)</strong>
                <div className="mt-1 text-slate-300">→ Luôn rút lời, lãi kép = thua chắc</div>
              </div>
              <div className="bg-yellow-900/30 p-3 rounded border border-yellow-600/50">
                <strong className="text-yellow-300">Win rate trung bình (40-60%)</strong>
                <div className="mt-1 text-slate-300">→ Tùy số chu kỳ, cần tính toán kỹ</div>
              </div>
              <div className="bg-green-900/30 p-3 rounded border border-green-600/50">
                <strong className="text-green-300">Win rate cao (&gt;60%)</strong>
                <div className="mt-1 text-slate-300">→ Ưu tiên tái đầu tư, lãi kép rất có lợi</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}