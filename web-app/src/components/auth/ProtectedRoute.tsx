'use client';

import { useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredRole?: string;
}

export default function ProtectedRoute({ 
  children, 
  requiredPermission,
  requiredRole 
}: ProtectedRouteProps) {
  const { user, loading, checkAuth } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  useEffect(() => {
    // Check permissions/roles when user is loaded
    if (user) {
      if (requiredPermission && !user.permissions.includes(requiredPermission)) {
        router.push('/unauthorized');
      }
      if (requiredRole && user.role !== requiredRole) {
        router.push('/unauthorized');
      }
    }
  }, [user, requiredPermission, requiredRole, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Check permissions
  if (requiredPermission && !user.permissions.includes(requiredPermission)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
          <p className="mt-2 text-gray-600">You do not have permission to access this page.</p>
        </div>
      </div>
    );
  }

  if (requiredRole && user.role !== requiredRole) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
          <p className="mt-2 text-gray-600">Your role does not have access to this page.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
