const riskConfig = {
  SAFE: { bg: 'bg-green-100', text: 'text-green-800', dot: 'bg-green-500' },
  MODERATE: { bg: 'bg-amber-100', text: 'text-amber-800', dot: 'bg-amber-500' },
  RISKY: { bg: 'bg-red-100', text: 'text-red-800', dot: 'bg-red-500' },
};

export default function RiskBadge({ risk, size = 'md' }) {
  const category = (risk || '').toUpperCase();
  const config = riskConfig[category] || riskConfig.MODERATE;
  const sizeClass = size === 'lg' ? 'px-4 py-2 text-base' : size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span className={`inline-flex items-center gap-1.5 font-semibold rounded-full ${config.bg} ${config.text} ${sizeClass}`}>
      <span className={`h-2 w-2 rounded-full ${config.dot}`} />
      {category}
    </span>
  );
}
