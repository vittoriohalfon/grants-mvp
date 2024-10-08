import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export function ThankYouPage() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <Card className="max-w-md w-full">
        <CardHeader>
          <CardTitle className="text-3xl font-bold text-center text-blue-600">Thank You!</CardTitle>
        </CardHeader>
        <CardContent>
          <h1 className="text-4xl font-bold mb-4">Thank You for Scheduling!</h1>
          <p className="text-xl mb-8">We&apos;ve received your information and are excited to help you find relevant grants for your business.</p>
          <p className="text-lg mb-4">Here&apos;s what to expect next:</p>
          <p className="text-center text-gray-700 mb-4">
            Your meeting has been successfully booked. We&apos;re excited to discuss grant opportunities with you!
          </p>
          <p className="text-center text-gray-600 text-sm">
            You&apos;ll receive a confirmation email shortly with the meeting details.
          </p>
          <p className="mb-4">We&apos;ll be in touch soon with more information about potential grant opportunities.</p>
        </CardContent>
      </Card>
    </div>
  )
}