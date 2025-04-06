import ChatComponent from './components/ChatComponent';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-6">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-800 mb-2">
            Personal Health AI Assistant
          </h1>
          <p className="text-gray-600">
            Your personal health companion powered by PinAI
          </p>
        </header>
        
        <div className="grid md:grid-cols-4 gap-6">
          <div className="md:col-span-1 space-y-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <h2 className="font-semibold text-blue-800 mb-2">About</h2>
              <p className="text-sm text-gray-600">
                Your personal health AI agent analyzes your health data to provide insights, 
                recommendations, and help you make informed decisions about your health.
              </p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <h2 className="font-semibold text-blue-800 mb-2">Features</h2>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Blood test analysis</li>
                <li>• Vital signs monitoring</li>
                <li>• Personalized health recommendations</li>
                <li>• Health risk assessments</li>
                <li>• Medication reminders</li>
              </ul>
            </div>
          </div>
          
          <div className="md:col-span-3">
            <ChatComponent />
          </div>
        </div>
        
        <footer className="mt-10 text-center text-sm text-gray-500">
          <p>
            Built with PinAI Agent SDK | 
            <a href="https://github.com/PIN-AI/pinai_agent_sdk" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </p>
        </footer>
      </div>
    </main>
  );
}
