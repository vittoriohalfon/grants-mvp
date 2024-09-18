"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Loader2, Search, Database, BarChart2 } from "lucide-react"

const steps = [
  { icon: Search, text: "Analyzing website structure..." },
  { icon: Loader2, text: "Gathering online information..." },
  { icon: Database, text: "Structuring data..." },
  { icon: BarChart2, text: "Generating insights..." },
]

export function LoadingComponent() {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prevStep) => (prevStep + 1) % steps.length)
      setProgress((prevProgress) => Math.min(prevProgress + 25, 100))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-8 bg-white rounded-xl shadow-lg">
        <h2 className="text-2xl font-bold text-center mb-6">Analyzing Your Website</h2>
        <div className="relative pt-1 mb-6">
          <div className="overflow-hidden h-2 text-xs flex rounded bg-blue-200">
            <motion.div
              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"
              style={{ width: `${progress}%` }}
              initial={{ width: "0%" }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
            />
          </div>
        </div>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              className={`flex items-center space-x-4 ${
                index === currentStep ? "text-blue-600" : "text-gray-400"
              }`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: index === currentStep ? 1 : 0.5, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <motion.div
                animate={{
                  rotate: index === currentStep ? 360 : 0,
                }}
                transition={{ duration: 2, repeat: index === currentStep ? Infinity : 0, ease: "linear" }}
              >
                <step.icon className="w-6 h-6" />
              </motion.div>
              <span className="font-medium">{step.text}</span>
            </motion.div>
          ))}
        </div>
        <motion.div
          className="mt-8 text-center text-gray-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 1 }}
        >
          Please wait while we process your website...
        </motion.div>
      </div>
    </div>
  )
}