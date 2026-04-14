'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { ListingForm } from '@/components/listings/listing-form';

export default function NewListingPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Link href="/listings" className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700">
          <ArrowLeft className="h-4 w-4" />
          Back to listings
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create a draft listing</h1>
          <p className="text-gray-500">
            Save the core property details first. Once the draft exists, you can continue with pricing
            rules, blackout dates, and photo uploads.
          </p>
        </div>
      </div>

      <ListingForm
        mode="create"
        onSuccess={(property) => router.push(`/listings/${property.id}/edit?created=1`)}
      />
    </div>
  );
}
