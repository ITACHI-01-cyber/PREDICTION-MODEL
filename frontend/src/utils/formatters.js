export function formatCurrency(value) {
  if (value == null) return '—';
  const num = Number(value);
  if (isNaN(num)) return '—';
  return `₹ ${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
}

export function formatPercentage(value) {
  if (value == null) return '—';
  const num = Number(value);
  if (isNaN(num)) return '—';
  return `${num.toFixed(1)}%`;
}

export function formatDate(dateString) {
  if (!dateString) return '—';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatMonths(value) {
  if (value == null) return '—';
  const num = Number(value);
  if (isNaN(num)) return '—';
  if (num === 1) return '1 month';
  return `${num.toFixed(1)} months`;
}
