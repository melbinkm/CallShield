import TabSelector from "./TabSelector";
import AudioUploader from "./AudioUploader";
import TranscriptPaster from "./TranscriptPaster";
import MicRecorder from "./MicRecorder";

type Tab = "upload" | "record" | "paste";

interface Props {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  onFileSelect: (file: File) => void;
  onTranscriptSubmit: (text: string) => void;
  disabled?: boolean;
  isRecording?: boolean;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  cumulativeScore?: number;
}

export default function InputPanel({
  activeTab,
  onTabChange,
  onFileSelect,
  onTranscriptSubmit,
  disabled,
  isRecording,
  onStartRecording,
  onStopRecording,
  cumulativeScore,
}: Props) {
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <TabSelector activeTab={activeTab} onTabChange={onTabChange} />
      <div className="p-6">
        {activeTab === "upload" && (
          <AudioUploader onFileSelect={onFileSelect} disabled={disabled} />
        )}
        {activeTab === "record" && (
          <MicRecorder
            isRecording={isRecording || false}
            onStart={onStartRecording || (() => {})}
            onStop={onStopRecording || (() => {})}
            cumulativeScore={cumulativeScore}
          />
        )}
        {activeTab === "paste" && (
          <TranscriptPaster onTranscriptSubmit={onTranscriptSubmit} disabled={disabled} />
        )}
      </div>
    </div>
  );
}
