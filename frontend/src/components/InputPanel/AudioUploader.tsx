import { useState, useRef } from "react";
import type { DragEvent } from "react";

interface Props {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export default function AudioUploader({ onFileSelect, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(file: File) {
    if (!file.name.toLowerCase().endsWith(".wav")) {
      alert("Only WAV files are accepted.");
      return;
    }
    setFileName(file.name);
    onFileSelect(file);
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={() => setIsDragging(false)}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
        isDragging
          ? "border-blue-500 bg-blue-500/10"
          : "border-gray-600 hover:border-gray-400"
      } ${disabled ? "opacity-50 pointer-events-none" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".wav"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {fileName ? (
        <p className="text-green-400 font-medium">{fileName}</p>
      ) : (
        <>
          <p className="text-gray-300 text-lg mb-2">
            Drop a WAV file here or click to browse
          </p>
          <p className="text-gray-500 text-sm">Max 25MB, WAV format only</p>
        </>
      )}
    </div>
  );
}
