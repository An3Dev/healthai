import ChatComponent from './components/ChatComponent';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-neutral-900 via-blue-950 to-neutral-900 dark:from-neutral-900 dark:via-blue-950 dark:to-neutral-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Hero Section with Floating Elements */}
        <header className="relative py-10 md:py-16 px-4 text-center mb-8 overflow-hidden">
          <div className="absolute inset-0 -z-10 overflow-hidden">
            <div className="absolute -top-10 -left-[10%] w-[30%] aspect-square rounded-full bg-primary/10 blur-3xl"></div>
            <div className="absolute top-[20%] -right-[5%] w-[25%] aspect-square rounded-full bg-secondary/10 blur-3xl"></div>
            <div className="absolute -bottom-20 left-[10%] w-[20%] aspect-square rounded-full bg-accent/10 blur-3xl"></div>
          </div>
          
          <div className="relative">
            <div className="inline-block animate-pulse bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent text-sm font-medium mb-2 px-3 py-1 rounded-full border border-neutral-700">
              AI-Powered Health Analysis
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
              Your Advanced Health Assistant
            </h1>
            <p className="text-neutral-300 max-w-2xl mx-auto text-lg">
              Personalized insights and recommendations powered by cutting-edge AI to help you understand and improve your health.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <a href="#chat" className="px-6 py-2.5 bg-gradient-to-r from-primary to-primary-dark text-white font-medium rounded-lg transition-all hover:shadow-lg hover:scale-105">
                Get Started
              </a>
              <a href="#features" className="px-6 py-2.5 bg-white/10 text-white font-medium rounded-lg border border-white/20 backdrop-blur-sm transition-all hover:bg-white/20">
                Learn More
              </a>
            </div>
          </div>
        </header>
        
        <div className="grid lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-3 space-y-6">
            <div className="glass p-6 rounded-2xl backdrop-blur border border-white/10">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 flex-shrink-0 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-white">
                    <path d="M10.5 21l-.6-.5C3.6 15.3 1 12.1 1 8.7 1 5.9 3.2 3.7 6 3.7c1.6 0 3.1.8 4 2 .9-1.2 2.4-2 4-2 2.8 0 5 2.2 5 5 0 3.4-2.6 6.6-9 11.9l-.5.4z" />
                  </svg>
                </div>
                <h2 className="font-semibold text-xl ml-3 text-white">HealthAI</h2>
              </div>
              <p className="text-neutral-300 text-sm">
                Your personal health AI agent analyzes your health data to provide insights, 
                recommendations, and help you make informed decisions.
              </p>
            </div>
            
            <div id="features" className="glass p-6 rounded-2xl border border-white/10">
              <h2 className="font-semibold text-lg mb-4 text-white flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 mr-2 text-primary">
                  <path d="M11.7 2.805a.75.75 0 01.6 0A60.65 60.65 0 0122.83 8.72a.75.75 0 01-.231 1.337 49.949 49.949 0 00-9.902 3.912l-.003.002-.34.18a.75.75 0 01-.707 0A50.009 50.009 0 007.5 12.174v-.224c0-.131.067-.248.172-.311a54.614 54.614 0 014.653-2.52.75.75 0 00-.65-1.352 56.129 56.129 0 00-4.78 2.589 1.858 1.858 0 00-.859 1.228 49.803 49.803 0 00-4.634-1.527.75.75 0 01-.231-1.337A60.653 60.653 0 0111.7 2.805z" />
                  <path d="M13.06 15.473a48.45 48.45 0 017.666-3.282c.134 1.414.22 2.843.255 4.285a.75.75 0 01-.46.71 47.878 47.878 0 00-8.105 4.342.75.75 0 01-.832 0 47.877 47.877 0 00-8.104-4.342.75.75 0 01-.461-.71c.035-1.442.121-2.87.255-4.286A48.4 48.4 0 016 13.18v1.27a1.5 1.5 0 00-.14 2.508c-.09.38-.222.753-.397 1.11.452.213.901.434 1.346.661a6.729 6.729 0 00.551-1.608 1.5 1.5 0 00.14-2.67v-.645a48.549 48.549 0 013.44 1.668 2.25 2.25 0 002.12 0z" />
                  <path d="M4.462 19.462c.42-.419.753-.89 1-1.394.453.213.902.434 1.347.661a6.743 6.743 0 01-1.286 1.794.75.75 0 11-1.06-1.06z" />
                </svg>
                Features
              </h2>
              <ul className="space-y-3 text-sm">
                {[
                  { name: 'Advanced blood test analysis', description: 'Get insights from your lab results' },
                  { name: 'Real-time vital signs monitoring', description: 'Track your health metrics as they change' },
                  { name: 'Personalized health recommendations', description: 'Receive tailored advice for your health goals' },
                  { name: 'Comprehensive risk assessments', description: 'Understand potential health concerns early' },
                  { name: 'Medication management & reminders', description: 'Never miss an important medication' },
                  { name: 'Health trend visualizations', description: 'See how your health changes over time' }
                ].map((feature, index) => (
                  <li key={index} className="flex items-start rounded-xl p-2 hover:bg-white/5 transition-colors">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary mr-3 flex-shrink-0">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                        <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                      </svg>
                    </span>
                    <div>
                      <span className="text-white font-medium block">{feature.name}</span>
                      <span className="text-neutral-400 text-xs">{feature.description}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="glass p-4 rounded-2xl border border-white/10">
              <h2 className="font-semibold text-sm mb-3 text-neutral-300">Quick Resources</h2>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { name: 'Health Encyclopedia', icon: '📚' },
                  { name: 'Medication Lookup', icon: '💊' },
                  { name: 'Symptom Checker', icon: '🔍' },
                  { name: 'Find a Doctor', icon: '👨‍⚕️' }
                ].map((resource, index) => (
                  <button key={index} className="p-3 rounded-xl bg-white/5 text-white text-left hover:bg-white/10 transition-colors">
                    <div className="text-xl mb-1">{resource.icon}</div>
                    <div className="text-xs font-medium">{resource.name}</div>
                  </button>
                ))}
              </div>
            </div>
          </aside>
          
          {/* Chat Component */}
          <div id="chat" className="lg:col-span-9">
            <ChatComponent />
          </div>
        </div>
        
        <footer className="mt-16 text-center text-sm text-neutral-400">
          <div className="flex items-center justify-center gap-4 mb-2">
            {['Privacy', 'Terms', 'Support', 'About'].map((item, i) => (
              <a key={i} href="#" className="hover:text-primary transition-colors">
                {item}
              </a>
            ))}
          </div>
          <p>
            Built with advanced AI technology | 
            <a href="https://github.com/PIN-AI/pinai_agent_sdk" className="text-primary hover:text-primary-dark transition-colors ml-1" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </p>
        </footer>
      </div>
    </main>
  );
}
