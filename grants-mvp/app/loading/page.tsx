'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LoadingComponent } from '@/components/loading'

export default function LoadingPage() {
  const router = useRouter()

  useEffect(() => {
    const triggerWorkflow = async () => {
      const processedUrl = localStorage.getItem('processingUrl')
      if (!processedUrl) {
        router.push('/')
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
        
        // Route to company profile after receiving the response
        router.push('/company-profile')
      } catch (error) {
        console.error('Error triggering workflow:', error)
        alert('An error occurred while processing your request. Please try again.')
        router.push('/')
      }
    }

    triggerWorkflow()
  }, [router])

  return <LoadingComponent />
}