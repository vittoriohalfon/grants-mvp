'use client';

import { SignUp } from "@clerk/nextjs";
import { useEffect } from 'react';
import { useSignUp } from "@clerk/nextjs";

export default function SignUpPage() {
    const { isLoaded, signUp, setActive } = useSignUp();

    useEffect(() => {
        if (!isLoaded) return;

        const associateProfile = async () => {
            const tempId = localStorage.getItem('tempProfileId');
            if (tempId && signUp?.status === 'complete') {
                try {
                    const response = await fetch('/api/associate-profile', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tempId }),
                    });

                    if (response.ok) {
                        localStorage.removeItem('tempProfileId');
                        // Set the active session after successful profile association
                        await setActive({ session: signUp.createdSessionId });
                    } else {
                        console.error('Failed to associate profile');
                    }
                } catch (error) {
                    console.error('Error associating profile:', error);
                }
            }
        };

        associateProfile();
    }, [isLoaded, signUp?.status, setActive]);

    if (!isLoaded) {
        return <div>Loading...</div>;
    }

    return (
        <SignUp 
            path="/sign-up" 
            routing="path" 
            signInUrl="/sign-in" 
            afterSignUpUrl="/profile"
        />
    );
}