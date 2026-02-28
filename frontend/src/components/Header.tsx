export default function Header() {
  return (
    <header className="bg-gray-900 text-white py-6 px-4 text-center">
      <h1 className="text-3xl font-bold tracking-tight">
        <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          CallShield
        </span>
      </h1>
      <p className="mt-2 text-gray-400 text-sm">
        AI-powered real-time phone scam detection using Mistral &amp; Voxtral
      </p>
      <span className="inline-block mt-3 text-xs font-medium px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
        Mistral AI Hackathon 2026
      </span>
    </header>
  );
}
