'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Building2, Shield, Zap, Users } from 'lucide-react';

const features = [
  {
    icon: Building2,
    title: 'Property Listings and Leasing',
    description: 'Manage rental listings, applications, lease workflows, and resident operations in one place.',
  },
  {
    icon: Shield,
    title: 'Secure by Default',
    description: 'Built-in authentication, authorization, and secure API endpoints.',
  },
  {
    icon: Zap,
    title: 'Fast and Modern',
    description: 'Built with Next.js, FastAPI, and Flutter for a responsive multi-surface experience.',
  },
  {
    icon: Users,
    title: 'Operationally Ready',
    description: 'Support for landlords, tenants, property managers, notifications, and role-aware access.',
  },
];

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="text-xl font-bold text-blue-600">MeroGhar</div>
            <div className="flex items-center gap-4">
              <Link href="/properties">
                <Button variant="ghost">Browse Properties</Button>
              </Link>
              <Link href="/login">
                <Button variant="ghost">Sign in</Button>
              </Link>
              <Link href="/signup">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="pt-16">
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              Rental operations built for real properties
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              MeroGhar helps landlords publish listings, tenants discover homes, and property managers run day-to-day operations from one platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/properties">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  Browse Properties
                </Button>
              </Link>
              <Link href="/signup">
                <Button size="lg" className="w-full sm:w-auto">
                  Start Free Trial
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="ghost" size="lg" className="w-full sm:w-auto">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </section>

        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
          <div className="max-w-7xl mx-auto">
              <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Everything You Need</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="p-6 rounded-xl border border-gray-200 hover:border-blue-500 hover:shadow-lg transition-all"
                >
                  <div className="h-12 w-12 rounded-lg bg-blue-50 flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Ready to Get Started?</h2>
              <p className="text-lg text-gray-600 mb-8">
                Launch your rental operations with the same backend, web, and mobile platform.
              </p>
            <Link href="/signup">
              <Button size="lg">Create Your Account</Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="py-8 px-4 border-t border-gray-200">
        <div className="max-w-7xl mx-auto text-center text-gray-500 text-sm">
          © {new Date().getFullYear()} MeroGhar. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
