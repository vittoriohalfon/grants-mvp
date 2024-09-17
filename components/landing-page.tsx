'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

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

      const { workflowId } = await response.json()

      // Store the workflowId in localStorage
      localStorage.setItem('workflowId', workflowId)

      //Navigate to the company profile page
      router.push('/company-profile')

    } catch (error) {
      console.error('Error triggering workflow:', error)
      // Handle error (e.g., show an error message to the user)
      alert('An error occurred while processing your request. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center px-4">
      <h1 className="text-5xl font-bold text-center mb-4 text-black">Skim</h1>
      <p className="text-xl text-center mb-8 max-w-2xl text-black">
        Connecting Innovators with Opportunity: AI-Powered Grant Matching for Business Growth
      </p>
      <form onSubmit={handleSubmit} className="w-full max-w-md">
        <div className="relative">
          <Input
            type="url"
            placeholder="Insert your business URL here"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="pr-20 text-black placeholder-gray-500"
            disabled={isLoading}
          />
          <Button 
            type="submit" 
            className="absolute right-0 top-0 bottom-0 rounded-l-none"
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : 'Enter'}
          </Button>
        </div>
      </form>
    </div>
  )
}