import React, { Suspense } from 'react';
import { CompanyProfileComponent } from '@/components/company-profile';

export default function CompanyProfilePage() {
  return (
    <main className="min-h-screen bg-gray-100">
      <Suspense fallback={<div>Loading...</div>}>
        <CompanyProfileComponent />
      </Suspense>
    </main>
  )
}