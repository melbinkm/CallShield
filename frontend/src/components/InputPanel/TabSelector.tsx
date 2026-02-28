type Tab = "upload" | "record" | "paste";

interface Props {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const tabs: { id: Tab; label: string }[] = [
  { id: "upload", label: "Upload Audio" },
  { id: "record", label: "Record" },
  { id: "paste", label: "Paste Transcript" },
];

export default function TabSelector({ activeTab, onTabChange }: Props) {
  return (
    <div className="flex border-b border-gray-700">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            activeTab === tab.id
              ? "text-white border-b-2 border-blue-500"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
