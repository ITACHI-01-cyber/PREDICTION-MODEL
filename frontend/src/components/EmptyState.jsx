import { InboxIcon } from 'lucide-react';

export default function EmptyState({ icon: Icon = InboxIcon, title = 'No data found', message = 'There are no items to display.' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="bg-gray-100 rounded-full p-4 mb-4">
        <Icon className="h-8 w-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 max-w-sm">{message}</p>
    </div>
  );
}
