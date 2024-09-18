'use client'

import { useState, useEffect, useRef } from 'react'
import { Loader2, Edit2 } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

// Update the dataStructure to match the API response
interface DataField {
  label: string;
  key: string;
  type: 'input' | 'textarea';
}

const dataStructure: { [key: string]: DataField[] } = {
  'Company Information': [
    { label: 'Company Name', key: 'company_name', type: 'input' },
    { label: 'Contact Email', key: 'contact_email', type: 'input' },
    { label: 'Industry Sector', key: 'industry_sector', type: 'input' },
  ],
  'Business Description': [
    { label: 'Company Overview', key: 'company_overview', type: 'textarea' },
    { label: 'Core Products/Services', key: 'core_products_or_services', type: 'textarea' },
    { label: 'Unique Selling Proposition (USP)', key: 'unique_selling_proposition', type: 'textarea' },
    { label: 'Company Vision/Mission', key: 'company_vision', type: 'textarea' },
  ],
  'Project or Innovation Information': [
    { label: 'Research & Development Activities', key: 'research_development_activities', type: 'textarea' },
  ],
  'Target Markets and Clients': [
    { label: 'Target Audience/Market', key: 'target_audience', type: 'textarea' },
    { label: 'Key Clients or Partners', key: 'key_clients_or_partners', type: 'textarea' },
    { label: 'Market Reach', key: 'market_reach', type: 'input' },
  ],
}

export function CompanyProfileComponent() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<Record<string, string> | null>(null)
  const [editMode, setEditMode] = useState<Record<string, boolean>>({})
  const calendlyScriptLoaded = useRef(false);

  useEffect(() => {
    const fetchData = async () => {
      const requestId = localStorage.getItem('requestId')
      if (!requestId) {
        window.location.href = '/'
        return
      }

      try {
        const response = await fetch(`/api/get-results?requestId=${requestId}`)
        if (response.ok) {
          const resultData = await response.json()
          setData(resultData)
          setLoading(false)
        } else if (response.status === 404) {
          // Results not ready yet, poll again after a delay
          setTimeout(fetchData, 1500)
        } else {
          throw new Error('Failed to fetch results')
        }
      } catch (error) {
        console.error('Error fetching results:', error)
        alert('An error occurred while fetching results. Please try again.')
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  useEffect(() => {
    if (!calendlyScriptLoaded.current) {
      const script = document.createElement('script');
      script.src = "https://assets.calendly.com/assets/external/widget.js";
      script.async = true;
      script.onload = () => {
        calendlyScriptLoaded.current = true;
      };
      document.body.appendChild(script);

      const link = document.createElement('link');
      link.href = "https://assets.calendly.com/assets/external/widget.css";
      link.rel = "stylesheet";
      document.head.appendChild(link);
    }
  }, []);

  const handleEdit = (key: string) => {
    setEditMode(prev => ({ ...prev, [key]: true }))
  }

  const handleSave = (key: string, value: string) => {
    setData(prev => prev ? { ...prev, [key]: value } : null)
    setEditMode(prev => ({ ...prev, [key]: false }))
  }

  const openCalendly = () => {
    if (typeof window !== 'undefined' && window.Calendly) {
      window.Calendly.initPopupWidget({
        url: 'https://calendly.com/justin-justskim/skim-discovery'
      });
    } else {
      console.error('Calendly widget is not available');
    }
  };

  const handleConfirm = async () => {
    try {
      openCalendly();
      const response = await fetch('/api/confirm-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to confirm profile');
      }

      // Handle successful confirmation (e.g., show a success message)
    } catch (error) {
      console.error('Error confirming profile:', error);
      alert('An error occurred while confirming your profile. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-500 mx-auto" />
          <p className="mt-4 text-lg text-gray-600">Analyzing your website...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Remove the Script component for Calendly */}
      <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-center mb-8">{data?.company_name}</h1>
          
          {Object.entries(dataStructure).map(([section, fields]) => (
            <Card key={section} className="mb-8">
              <CardHeader>
                <CardTitle>{section}</CardTitle>
              </CardHeader>
              <CardContent>
                {fields.map(({ label, key, type }) => (
                  <div key={key} className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                    {editMode[key] ? (
                      <div className="flex flex-col space-y-2">
                        {type === 'textarea' ? (
                          <Textarea 
                            value={data?.[key] || ''}
                            onChange={(e) => setData(prev => prev ? {...prev, [key]: e.target.value} : null)}
                            className="min-h-[100px]"
                          />
                        ) : (
                          <Input 
                            value={data?.[key] || ''}
                            onChange={(e) => setData(prev => prev ? {...prev, [key]: e.target.value} : null)}
                          />
                        )}
                        <Button onClick={() => handleSave(key, data?.[key] || '')} className="self-end">
                          Save Changes
                        </Button>
                      </div>
                    ) : (
                      <div className="flex justify-between items-start">
                        <p className="text-gray-900 whitespace-pre-wrap">{data?.[key]}</p>
                        <Button onClick={() => handleEdit(key)} variant="ghost" size="sm" className="mt-1">
                          <Edit2 className="h-4 w-4 mr-2" />
                          Edit
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
          
          <Button onClick={handleConfirm} className="w-full py-6 text-lg">
            Confirm Information and Find Grants
          </Button>
        </div>
      </div>
    </>
  )
}