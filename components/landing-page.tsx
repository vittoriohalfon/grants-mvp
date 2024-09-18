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
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch('/api/trigger-workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain: url }),
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
    <div className="flex flex-col min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <Link className="flex items-center justify-center" href="#">
              <FileTextIcon className="h-6 w-6 mr-2" />
              <span className="font-bold text-xl">Skim</span>
            </Link>
            <nav className="flex gap-4 sm:gap-6">
              <Link className="text-sm font-medium hover:text-primary" href="#">Features</Link>
              <Link className="text-sm font-medium hover:text-primary" href="#">Pricing</Link>
              <Link className="text-sm font-medium hover:text-primary" href="#">About</Link>
              <Link className="text-sm font-medium hover:text-primary" href="#">Contact</Link>
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 flex items-center">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="space-y-2">
                <Image
                  src="/logo.png"
                  alt="Skim Logo"
                  width={200}
                  height={200}
                  className="mx-auto mb-8"
                />
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none">
                  AI for Government Grants
                </h1>
                <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
                  Skim leverages AI to help you find, manage, and bid on federal, state, local, and education government opportunities.
                </p>
              </div>
              <div className="w-full max-w-md mx-auto space-y-2">
                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                  <Input
                    type="url"
                    placeholder="Insert your business URL here"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="flex-1"
                    disabled={isLoading}
                  />
                  <Button type="submit" disabled={isLoading} className="w-full sm:w-auto">
                    {isLoading ? 'Processing...' : 'Enter'}
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </section>
        
        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 bg-muted flex items-center">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-12">
              How Skim Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { icon: SearchIcon, title: "Find Opportunities", description: "Discover relevant government contracts and grants tailored to your business." },
                { icon: FileTextIcon, title: "Generate Proposals", description: "Use AI to create compelling and competitive proposals quickly." },
                { icon: AwardIcon, title: "Win Contracts", description: "Increase your chances of winning with optimized bids and proposals." }
              ].map((item, index) => (
                <div key={index} className="flex flex-col items-center text-center">
                  <item.icon className="h-12 w-12 mb-4 text-primary" />
                  <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 flex items-center">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-12">
              What Our Clients Say
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { name: "John Doe", role: "CEO of TechSolutions Inc.", quote: "Skim has revolutionized our contracting process." },
                { name: "Jane Smith", role: "CFO of BuildRight Construction", quote: "We've doubled our contract win rate with Skim." },
                { name: "Mike Johnson", role: "Owner of GreenLeaf Landscaping", quote: "Skim's AI-powered proposals are game-changing." }
              ].map((testimonial, index) => (
                <div key={index} className="flex flex-col items-center text-center">
                  <Image
                    alt={testimonial.name}
                    className="rounded-full mb-4"
                    height={80}
                    src="/placeholder.svg?height=80&width=80"
                    style={{
                      aspectRatio: "80/80",
                      objectFit: "cover",
                    }}
                    width={80}
                  />
                  <p className="text-lg font-semibold mb-2">"{testimonial.quote}"</p>
                  <p className="text-sm text-muted-foreground">{testimonial.name}, {testimonial.role}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
        
        <section className="w-full py-24 md:py-32 lg:py-48 xl:py-64 bg-muted flex items-center">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                  Ready to win more contracts?
                </h2>
                <p className="mx-auto max-w-[600px] text-muted-foreground md:text-xl">
                  Join Skim today and start leveraging AI to boost your government contracting success.
                </p>
              </div>
              <div className="w-full max-w-md mx-auto space-y-2">
                <form className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                  <Input className="flex-1" placeholder="Enter your email" type="email" />
                  <Button type="submit" className="w-full sm:w-auto">Get Started</Button>
                </form>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t bg-muted">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center py-6">
            <p className="text-xs text-muted-foreground">© 2023 Skim. All rights reserved.</p>
            <nav className="flex gap-4 sm:gap-6 mt-4 sm:mt-0">
              <Link className="text-xs text-muted-foreground hover:underline underline-offset-4" href="#">
                Terms of Service
              </Link>
              <Link className="text-xs text-muted-foreground hover:underline underline-offset-4" href="#">
                Privacy
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  )
}