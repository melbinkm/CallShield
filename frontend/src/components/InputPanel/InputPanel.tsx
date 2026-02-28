import TabSelector from "./TabSelector";
import AudioUploader from "./AudioUploader";
import TranscriptPaster from "./TranscriptPaster";

type Tab = "upload" | "record" | "paste";

interface Props {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  onFileSelect: (file: File) => void;
  onTranscriptSubmit: (text: string) => void;
  disabled?: boolean;
}

export default function InputPanel({
  activeTab,
  onTabChange,
  onFileSelect,
  onTranscriptSubmit,
  disabled,
}: Props) {
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <TabSelector activeTab={activeTab} onTabChange={onTabChange} />
      <div className="p-6">
        {activeTab === "upload" && (
          <AudioUploader onFileSelect={onFileSelect} disabled={disabled} />
        )}
        {activeTab === "record" && (
          <div className="text-center text-gray-400 py-12">
            Mic recording coming in Phase 10
          </div>
        )}
        {activeTab === "paste" && (
          <TranscriptPaster onTranscriptSubmit={onTranscriptSubmit} disabled={disabled} />
        )}
      </div>
    </div>
  );
}
