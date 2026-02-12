import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Calculator, Zap, Thermometer, Ruler, Weight } from 'lucide-react';
import { Card } from '@/components/ui';

interface CalcResult { label: string; value: string; unit: string; }

export default function EngineeringCalculatorPage() {
  const [calcType, setCalcType] = useState<'current' | 'voltage' | 'size'>('current');
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [results, setResults] = useState<CalcResult[]>([]);

  const calcs = [
    { id: 'current' as const, name: 'Current Capacity', icon: Zap, desc: 'Calculate cable current-carrying capacity' },
    { id: 'voltage' as const, name: 'Voltage Drop', icon: Thermometer, desc: 'Calculate voltage drop for given length' },
    { id: 'size' as const, name: 'Cable Sizing', icon: Ruler, desc: 'Determine optimal cable size for load' },
  ];

  const inputFields: Record<string, { label: string; placeholder: string; unit: string }[]> = {
    current: [
      { label: 'Cross Section Area', placeholder: '240', unit: 'mm²' },
      { label: 'Conductor Material', placeholder: 'Copper', unit: '' },
      { label: 'Installation Method', placeholder: 'Trefoil', unit: '' },
      { label: 'Ambient Temperature', placeholder: '40', unit: '°C' },
    ],
    voltage: [
      { label: 'Load Current', placeholder: '500', unit: 'A' },
      { label: 'Cable Length', placeholder: '100', unit: 'm' },
      { label: 'Cable Size', placeholder: '240', unit: 'mm²' },
      { label: 'Power Factor', placeholder: '0.85', unit: '' },
    ],
    size: [
      { label: 'Load Power', placeholder: '250', unit: 'kW' },
      { label: 'System Voltage', placeholder: '11', unit: 'kV' },
      { label: 'Cable Length', placeholder: '200', unit: 'm' },
      { label: 'Max Voltage Drop', placeholder: '5', unit: '%' },
    ],
  };

  const calculate = () => {
    const mockResults: Record<string, CalcResult[]> = {
      current: [
        { label: 'Rated Current (in air)', value: '546', unit: 'A' },
        { label: 'Derated Current', value: '478', unit: 'A' },
        { label: 'Derating Factor', value: '0.875', unit: '' },
        { label: 'Recommended Cable', value: 'HAK-XLPE-240', unit: '' },
      ],
      voltage: [
        { label: 'Voltage Drop', value: '3.2', unit: '%' },
        { label: 'Drop per km', value: '0.32', unit: 'V/m' },
        { label: 'Receiving End Voltage', value: '10,648', unit: 'V' },
        { label: 'Status', value: 'Within 5% limit', unit: '' },
      ],
      size: [
        { label: 'Minimum Size (thermal)', value: '120', unit: 'mm²' },
        { label: 'Minimum Size (vdrop)', value: '185', unit: 'mm²' },
        { label: 'Recommended Size', value: '185', unit: 'mm²' },
        { label: 'Estimated Weight', value: '3,250', unit: 'kg/km' },
      ],
    };
    setResults(mockResults[calcType] ?? []);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Engineering Calculator</h1><p className="text-body text-muted-silver">Cable sizing, current capacity & voltage drop tools</p></div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {calcs.map((c) => (
          <Card key={c.id} variant="glass" className={`p-4 cursor-pointer transition-all ${calcType === c.id ? 'ring-1 ring-electric-cyan/40' : 'hover:bg-steel-slate/5'}`} onClick={() => { setCalcType(c.id); setResults([]); }}>
            <c.icon size={20} className={`${calcType === c.id ? 'text-electric-cyan' : 'text-muted-silver'} mb-2`} />
            <h3 className="text-sm font-semibold text-ghost-white">{c.name}</h3>
            <p className="text-[10px] text-muted-silver mt-1">{c.desc}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card variant="glass" className="p-5 space-y-4">
          <h3 className="text-sm font-semibold text-ghost-white flex items-center gap-2"><Calculator size={14} className="text-electric-cyan" />Input Parameters</h3>
          <div className="space-y-3">
            {(inputFields[calcType] ?? []).map((f, i) => (
              <div key={i}>
                <label className="text-xs text-muted-silver block mb-1">{f.label} {f.unit && <span className="text-electric-cyan">({f.unit})</span>}</label>
                <input value={inputs[`${calcType}-${i}`] ?? ''} onChange={(e) => setInputs({ ...inputs, [`${calcType}-${i}`]: e.target.value })} placeholder={f.placeholder} className="w-full bg-deep-navy/50 border border-steel-slate/20 rounded-lg px-3 py-2 text-sm text-ghost-white placeholder:text-muted-silver/50 focus:outline-none focus:ring-1 focus:ring-electric-cyan/40" />
              </div>
            ))}
          </div>
          <button onClick={calculate} className="w-full bg-electric-cyan/20 text-electric-cyan px-4 py-2.5 rounded-lg hover:bg-electric-cyan/30 transition-colors text-sm font-medium">Calculate</button>
        </Card>

        <Card variant="glass" className="p-5">
          <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><Weight size={14} className="text-neon-emerald" />Results</h3>
          {results.length > 0 ? (
            <div className="space-y-3">
              {results.map((r, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} className="flex items-center justify-between p-3 bg-deep-navy/40 rounded-lg">
                  <span className="text-xs text-muted-silver">{r.label}</span>
                  <span className="text-sm font-bold text-ghost-white">{r.value} <span className="text-xs text-electric-cyan">{r.unit}</span></span>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-muted-silver/40">
              <Calculator size={32} className="mb-2" />
              <p className="text-xs">Enter parameters and click Calculate</p>
            </div>
          )}
        </Card>
      </div>
    </motion.div>
  );
}
