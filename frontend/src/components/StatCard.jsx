export default function StatCard({ icon: Icon, label, value, change, iconBg = 'bg-blue-100', iconColor = 'text-blue-600' }) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`${iconBg} rounded-lg p-3 shrink-0`}>
        <Icon className={`h-6 w-6 ${iconColor}`} />
      </div>
      <div className="min-w-0">
        <p className="text-sm text-gray-600 truncate">{label}</p>
        <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        {change !== undefined && change !== null && (
          <p className={`text-sm mt-1 ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '+' : ''}
            {change}% from last month
          </p>
        )}
      </div>
    </div>
  );
}
