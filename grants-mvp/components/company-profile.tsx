'use client'

import { useState, useEffect } from 'react'
import { Edit2 } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { LoadingComponent } from './loading'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import ReactMarkdown from 'react-markdown'

interface DataField {
  label: React.ReactNode;
  key: string;
  type: 'input' | 'textarea';
  promptIndex: number;
}

interface Result {
  prompt: string;
  answer: string;
}

interface ResultData {
  domain: string;
  results: Result[];
}

const dataStructure: { [key: string]: DataField[] } = {
  'Company Details': [
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Company Name</span>, key: 'company_name', type: 'input', promptIndex: 0 },
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Contact Email</span>, key: 'contact_email', type: 'input', promptIndex: -1 },
  ],
  'Company Information': [
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Industry Sector</span>, key: 'industry_sector', type: 'textarea', promptIndex: 1 },
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Company Overview</span>, key: 'company_overview', type: 'textarea', promptIndex: 2 },
  ],
  'Products and Services': [
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Core Products/Services</span>, key: 'core_products_or_services', type: 'textarea', promptIndex: 3 },
  ],
  'Unique Selling Proposition': [
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Unique Selling Proposition</span>, key: 'unique_selling_proposition', type: 'textarea', promptIndex: 4 },
  ],
  'Research and Development': [
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Research & Development Activities</span>, key: 'research_development_activities', type: 'textarea', promptIndex: 5 },
  ],
  'Target Audience': [
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Target Audience</span>, key: 'target_audience', type: 'textarea', promptIndex: 6 },
  ],
  'Key Clients and Partners': [
    { label: <span className="title-emphasis" style={{ textDecoration: 'underline' }}>Key Clients/Partners</span>, key: 'key_clients_partners', type: 'textarea', promptIndex: 7 },
  ],
}

export function CompanyProfileComponent() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<Record<string, string> | null>(null)
  const [editMode, setEditMode] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string>>({});

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
          const resultData: ResultData = await response.json()
          const formattedData: Record<string, string> = {
            domain: resultData.domain,
            contact_email: '',
            research_development_activities: '',
          }
          resultData.results.forEach((result: Result, index: number) => {
            const key = Object.values(dataStructure).flat().find(field => field.promptIndex === index)?.key
            if (key) {
              formattedData[key] = result.answer
            }
          })
          setData(formattedData)
          setLoading(false)
        } else if (response.status === 404) {
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

  const handleEdit = (key: string) => {
    setEditMode(prev => ({ ...prev, [key]: true }))
  }

  const handleSave = (key: string, value: string) => {
    setData(prev => prev ? { ...prev, [key]: value } : null)
    setEditMode(prev => ({ ...prev, [key]: false }))
  }

  const validateMandatoryFields = () => {
    const newErrors: Record<string, string> = {};
    
    if (!data?.contact_email) {
      newErrors.contact_email = "Contact Email is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleConfirm = async () => {
    if (!validateMandatoryFields()) {
      return;
    }

    try {
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

      // Redirect to sign-in page after successful confirmation
      window.location.href = 'http://localhost:3000/sign-in';
    } catch (error) {
      console.error('Error confirming profile:', error);
      alert('An error occurred while confirming your profile. Please try again.');
    }
  };

  if (loading) {
    return <LoadingComponent />
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#05071A] to-[#0A0E2E] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8 text-white">{data?.company_name}</h1>
        
        {Object.entries(dataStructure).map(([section, fields]) => (
          <Card key={section} className="mb-8 bg-[#10153E] border-gray-700 shadow-lg">
            <CardHeader>
              <CardTitle className="text-white">{section}</CardTitle>
            </CardHeader>
            <CardContent>
              {fields.map(({ label, key, type }) => (
                <div key={key} className="mb-4">
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    {label}
                    {key === 'contact_email' && (
                      <span className="text-red-400 ml-1">*</span>
                    )}
                  </label>
                  {editMode[key] ? (
                    <div className="flex flex-col space-y-2">
                      {type === 'textarea' ? (
                        <Textarea 
                          value={data?.[key] || ''}
                          onChange={(e) => {
                            setData(prev => prev ? {...prev, [key]: e.target.value} : null);
                            setErrors(prev => ({...prev, [key]: ''}));
                          }}
                          className={`min-h-[100px] bg-[#1C2147] text-white border-gray-600 ${errors[key] ? 'border-red-500' : ''}`}
                        />
                      ) : (
                        <Input 
                          value={data?.[key] || ''}
                          onChange={(e) => {
                            setData(prev => prev ? {...prev, [key]: e.target.value} : null);
                            setErrors(prev => ({...prev, [key]: ''}));
                          }}
                          className={`bg-[#1C2147] text-white border-gray-600 ${errors[key] ? 'border-red-500' : ''}`}
                        />
                      )}
                      {errors[key] && <p className="text-red-400 text-sm">{errors[key]}</p>}
                      <Button onClick={() => handleSave(key, data?.[key] || '')} className="self-end bg-blue-500 hover:bg-blue-600 text-white">
                        Save Changes
                      </Button>
                    </div>
                  ) : (
                    <div className="flex justify-between items-start">
                      <ReactMarkdown className="text-gray-200 whitespace-pre-wrap">
                        {data?.[key] || ''}
                      </ReactMarkdown>
                      <Button onClick={() => handleEdit(key)} variant="ghost" size="sm" className="mt-1 text-blue-400 hover:text-blue-300">
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
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="w-full">
                <Button 
                  onClick={handleConfirm} 
                  className="w-full py-6 text-lg bg-blue-500 hover:bg-blue-600 text-white"
                  disabled={!data?.contact_email || !data?.research_development_activities}
                >
                  Confirm Information and Find Grants
                </Button>
              </div>
            </TooltipTrigger>
            <TooltipContent className="bg-[#1C2147] text-white border-gray-600">
              <p>Please fill out the required field: Contact Email</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  )
}