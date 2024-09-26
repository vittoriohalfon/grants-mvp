'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@clerk/nextjs';
import { CompanyProfileComponent } from '@/components/company-profile';

export default function ProfilePage() {
  const { user, isLoaded } = useUser();
  const [profileData, setProfileData] = useState<Record<string, string> | null>(null);

  useEffect(() => {
    const fetchProfileData = async () => {
      if (isLoaded && user) {
        try {
          const response = await fetch('/api/get-profile');
          if (response.ok) {
            const data = await response.json();
            setProfileData(data);
          }
        } catch (error) {
          console.error('Error fetching profile data:', error);
        }
      }
    };

    fetchProfileData();
  }, [isLoaded, user]);

  if (!isLoaded || !user) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Your Profile</h1>
      <CompanyProfileComponent initialData={profileData as Record<string, string>} />
    </div>
  );
}