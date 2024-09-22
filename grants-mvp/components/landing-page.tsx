'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { SearchIcon, FileTextIcon, AwardIcon } from "lucide-react"
import Link from "next/link"
import Image from 'next/image'

export function LandingPageComponent() {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const preprocessUrl = (input: string): string => {
    let processedUrl = input.trim().toLowerCase()
    
    if (!processedUrl.startsWith('http://') && !processedUrl.startsWith('https://')) {
      processedUrl = 'https://' + processedUrl
    }
    
    processedUrl = processedUrl.replace(/\/$/, '')
    processedUrl = processedUrl.replace(/^(https?:\/\/)www\./, '$1')
    
    return processedUrl
  }

  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    let processedUrl = preprocessUrl(url)

    if (!isValidUrl(processedUrl)) {
      processedUrl = `https://${processedUrl}`
    }

    if (!isValidUrl(processedUrl)) {
      setError('Please enter a valid URL')
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch('/api/trigger-workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain: processedUrl }),
      })

      if (!response.ok) {
        throw new Error('Failed to process data')
      }

      const { requestId } = await response.json()
      localStorage.setItem('requestId', requestId)
      router.push('/company-profile')
    } catch (error) {
      console.error('Error triggering workflow:', error)
      alert('An error occurred while processing your request. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-[#05071A] to-[#0A0E2E]">
      <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-[#05071A]/80 backdrop-blur-md shadow-sm">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <Link className="flex items-center justify-center" href="#">
              <Image
                src="/logo.png"
                alt="Skim AI Logo"
                width={100}
                height={100}
                className="mr-2"
              />
              <span className="font-bold text-2xl text-white">Skim AI</span>
            </Link>
            <nav className="hidden md:flex gap-6">
              <Link className="text-sm font-medium text-gray-300 hover:text-blue-400 transition-colors" href="#">Features</Link>
              <Link className="text-sm font-medium text-gray-300 hover:text-blue-400 transition-colors" href="#">Pricing</Link>
              <Link className="text-sm font-medium text-gray-300 hover:text-blue-400 transition-colors" href="#">About</Link>
              <Link className="text-sm font-medium text-gray-300 hover:text-blue-400 transition-colors" href="#">Contact</Link>
            </nav>
            <Button className="hidden md:inline-flex bg-blue-500 hover:bg-blue-600 text-white">Get Started</Button>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 flex items-center bg-gradient-to-br from-[#05071A] via-[#0A0E2E] to-[#10153E]">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center space-y-8 text-center">
              <div className="space-y-4">
                <h1 className="text-5xl font-extrabold tracking-tighter sm:text-6xl md:text-7xl lg:text-8xl/none bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                  Skim AI
                </h1>
                <p className="text-2xl font-semibold text-gray-200">AI for Government Grants</p>
                <p className="mx-auto max-w-[700px] text-gray-300 md:text-xl">
                  Leverage AI to find, manage, and bid on federal, state, local, and education government opportunities with unprecedented efficiency.
                </p>
              </div>
              <div className="w-full max-w-md mx-auto space-y-4">
                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                  <Input
                    type="text"
                    placeholder="Insert your business URL here"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="flex-1 bg-white/10 backdrop-blur-sm border-gray-600 text-white placeholder-gray-400 focus:border-blue-400 focus:ring focus:ring-blue-300 focus:ring-opacity-50"
                    disabled={isLoading}
                  />
                  <Button type="submit" disabled={isLoading} className="w-full sm:w-auto bg-blue-500 hover:bg-blue-600 text-white">
                    {isLoading ? 'Processing...' : 'Get Started'}
                  </Button>
                </form>
                {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
              </div>
            </div>
          </div>
        </section>
        
        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 bg-[#0A0E2E] flex items-center">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-16 text-white">
              How Skim AI Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              {[
                { icon: SearchIcon, title: "Find Opportunities", description: "Discover relevant government contracts and grants tailored to your business." },
                { icon: FileTextIcon, title: "Generate Proposals", description: "Use AI to create compelling and competitive proposals quickly." },
                { icon: AwardIcon, title: "Win Contracts", description: "Increase your chances of winning with optimized bids and proposals." }
              ].map((item, index) => (
                <div key={index} className="flex flex-col items-center text-center group">
                  <div className="mb-6 p-4 bg-blue-900 rounded-full transition-all duration-300 group-hover:bg-blue-700">
                    <item.icon className="h-10 w-10 text-blue-400 transition-all duration-300 group-hover:text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-3 text-white">{item.title}</h3>
                  <p className="text-gray-300">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 flex items-center bg-gradient-to-br from-[#05071A] to-[#0A0E2E]">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-16 text-white">
              What Our Clients Say
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              {[
                { name: "John Doe", role: "CEO of TechSolutions Inc.", quote: "Skim AI has revolutionized our contracting process." },
                { name: "Jane Smith", role: "CFO of BuildRight Construction", quote: "We've doubled our contract win rate with Skim AI." },
                { name: "Mike Johnson", role: "Owner of GreenLeaf Landscaping", quote: "Skim AI's AI-powered proposals are game-changing." }
              ].map((testimonial, index) => (
                <div key={index} className="flex flex-col items-center text-center bg-[#10153E] p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <Image
                    alt={testimonial.name}
                    className="rounded-full mb-6 border-4 border-blue-900"
                    height={100}
                    src="/placeholder.svg?height=100&width=100"
                    style={{
                      aspectRatio: "100/100",
                      objectFit: "cover",
                    }}
                    width={100}
                  />
                  <p className="text-lg font-semibold mb-4 text-white">&ldquo;{testimonial.quote}&rdquo;</p>
                  <p className="text-sm text-gray-300">{testimonial.name}</p>
                  <p className="text-xs text-gray-400">{testimonial.role}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
        
        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 bg-blue-900 flex items-center">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center space-y-8 text-center">
              <div className="space-y-4">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-white">
                  Ready to win more contracts?
                </h2>
                <p className="mx-auto max-w-[600px] text-blue-200 md:text-xl">
                  Join Skim AI today and start leveraging AI to boost your government contracting success.
                </p>
              </div>
              <div className="w-full max-w-md mx-auto space-y-4">
                <form className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <Input className="flex-1 bg-white/10 backdrop-blur-sm border-blue-700 text-white placeholder-blue-300" placeholder="Enter your email" type="email" />
                  <Button type="submit" className="w-full sm:w-auto bg-white text-blue-900 hover:bg-blue-100">Get Started</Button>
                </form>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t border-gray-800 bg-[#05071A]">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center py-8">
            <div className="flex items-center mb-4 sm:mb-0">
              <Image
                src="/logo.png"
                alt="Skim AI Logo"
                width={24}
                height={24}
                className="mr-2"
              />
              <span className="font-bold text-xl text-white">Skim AI</span>
            </div>
            <p className="text-sm text-gray-400">© 2023 Skim AI. All rights reserved.</p>
            <nav className="flex gap-6 mt-4 sm:mt-0">
              <Link className="text-sm text-gray-400 hover:text-blue-400 transition-colors" href="#">
                Terms of Service
              </Link>
              <Link className="text-sm text-gray-400 hover:text-blue-400 transition-colors" href="#">
                Privacy Policy
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  )
}