# Skill: Integrate Saman Authentication (Legacy SSO)

## Context
 You are integrating a new frontend application (React, Vue, Vite, etc.) with the existing "Saman" ecosystem.
 The goal is to enforce authentication by checking for the existence of a valid session in `localStorage` shared from the parent domain (`saman.lafortuna.com.co`).

## Requirements
 1. **Auth Guard:** Create a mechanism to block access to the app if the user is not authenticated in Saman.
 2. **Shared Storage:** Read `localStorage.getItem('identity')`.
 3. **Validation:** Ensure the identity object contains a valid `token`.
 4. **Localhost Bypass:** If running on `localhost` or `127.0.0.1`, skip the check to facilitate development.
 5. **Redirect:** If check fails, redirect the user to `https://saman.lafortuna.com.co`.
 6. **UI:** Add a "CÉNTRICA" back button in the main navigation (Sidebar/Header) pointing to `https://saman.lafortuna.com.co/#/home`.

## example

### example React/Next.js (AuthProvider)
 Create `src/components/AuthProvider.tsx`:
 ```tsx
 "use client";
 import { useEffect, useState } from "react";

 export default function AuthProvider({ children }: { children: React.ReactNode }) {
   const [isAuthenticated, setIsAuthenticated] = useState(false);
   const [isLoading, setIsLoading] = useState(true);

   useEffect(() => {
     // 1. Bypass Localhost
     if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
       setIsAuthenticated(true);
       setIsLoading(false);
       return;
     }

     // 2. Check Identity
     try {
       const identityStr = localStorage.getItem("identity");
       if (!identityStr) throw new Error("No identity");
       
       const identity = JSON.parse(identityStr);
       if (!identity?.token) throw new Error("No token");

       setIsAuthenticated(true);
     } catch (e) {
       window.location.href = "https://saman.lafortuna.com.co";
     } finally {
       setIsLoading(false);
     }
   }, []);

   if (isLoading) return <div>Loading...</div>;
   if (!isAuthenticated) return null;

   return <>{children}</>;
 }
 ```
 *Usage:* Wrap your root layout or App component with `<AuthProvider>`.

### 2. Vue.js / Vite (Router Guard)
 In `router/index.ts` or `main.ts`:
 ```typescript
 router.beforeEach((to, from, next) => {
   if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
     return next();
   }

   const identityStr = localStorage.getItem('identity');
   if (!identityStr) {
     window.location.href = 'https://saman.lafortuna.com.co';
     return;
   }

   try {
     const identity = JSON.parse(identityStr);
     if (!identity.token) throw new Error('No token');
     next();
   } catch (e) {
     window.location.href = 'https://saman.lafortuna.com.co';
   }
 });
 ```

### 3. Back Button (Sidebar)
 Add a link with the class appropriate for your project:
 - **URL:** `https://saman.lafortuna.com.co/#/home`
 - **Text:** "CÉNTRICA"
 - **Icon:** Left Arrow
