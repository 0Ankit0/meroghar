'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, Eye, Pencil, Plus, Rocket, Trash2 } from 'lucide-react';
import { Button, Skeleton } from '@/components/ui';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  useDeleteListing,
  useLandlordListings,
  usePublishListing,
  useUnpublishListing,
} from '@/hooks/use-properties';
import {
  formatPropertyStatus,
  propertyStatusTone,
} from '@/lib/properties';
import { useAuthStore } from '@/store/auth-store';

function parsePage(value: string | null) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

function canManageListings(roles: string[] | undefined, isSuperuser: boolean | undefined) {
  if (isSuperuser) {
    return true;
  }

  if (!roles || roles.length === 0) {
    return true;
  }

  return roles.some((role) => /landlord|owner|admin/i.test(role));
}

export default function ListingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const page = parsePage(searchParams.get('page'));

  const user = useAuthStore((state) => state.user);
  const { data, isLoading, error } = useLandlordListings({ page, per_page: 20 });
  const publishListing = usePublishListing();
  const unpublishListing = useUnpublishListing();
  const deleteListing = useDeleteListing();

  const properties = data?.items ?? [];
  const publishedCount = properties.filter((property) => property.is_published).length;
  const draftCount = properties.filter((property) => !property.is_published).length;
  const showRoleHint = !canManageListings(user?.roles, user?.is_superuser);

  const goToPage = (nextPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    if (nextPage > 1) {
      params.set('page', String(nextPage));
    } else {
      params.delete('page');
    }
    router.push(params.toString() ? `/listings?${params.toString()}` : '/listings');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Listings</h1>
          <p className="text-gray-500">
            Create drafts, publish finished homes, and keep pricing-ready properties organised.
          </p>
        </div>
        <Link href="/listings/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New listing
          </Button>
        </Link>
      </div>

      {showRoleHint ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          This workspace is optimised for landlord roles. If your account is tenant-only, the backend
          may return a permission error for listing actions.
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: 'Listings on this page', value: properties.length },
          { label: 'Published now', value: publishedCount },
          { label: 'Draft or unpublished', value: draftCount },
        ].map((metric) => (
          <Card key={metric.label}>
            <CardContent className="pt-6">
              <p className="text-sm text-gray-500">{metric.label}</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">{metric.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-xl">Manage properties</CardTitle>
          {data ? (
            <span className="text-sm text-gray-500">
              Total returned: {data.total}
            </span>
          ) : null}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((key) => (
                <Skeleton key={key} className="h-16 w-full rounded-xl" />
              ))}
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-6 text-sm text-red-700">
              Unable to load your listings right now. Check your permissions or retry shortly.
            </div>
          ) : properties.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[840px]">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Listing</th>
                    <th className="pb-3 font-medium">Category</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Location</th>
                    <th className="pb-3 font-medium">Updated</th>
                    <th className="pb-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {properties.map((property) => (
                    <tr key={property.id} className="border-b border-gray-100 align-top last:border-0">
                      <td className="py-4">
                        <div>
                          <p className="font-medium text-gray-900">{property.name}</p>
                          <p className="mt-1 text-sm text-gray-500">{property.id}</p>
                        </div>
                      </td>
                      <td className="py-4 text-sm text-gray-600">
                        {property.category?.name ?? '—'}
                      </td>
                      <td className="py-4">
                        <span
                          className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${propertyStatusTone(property.status, property.is_published)}`}
                        >
                          {formatPropertyStatus(property.status, property.is_published)}
                        </span>
                      </td>
                      <td className="py-4 text-sm text-gray-600">
                        {property.location_address ?? '—'}
                      </td>
                      <td className="py-4 text-sm text-gray-600">
                        {property.updated_at ? new Date(property.updated_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-4">
                        <div className="flex flex-wrap justify-end gap-2">
                          <Link href={`/listings/${property.id}/edit`}>
                            <Button variant="outline" size="sm">
                              <Pencil className="mr-1 h-3.5 w-3.5" />
                              Edit
                            </Button>
                          </Link>
                          <Link href={`/properties/${property.id}`}>
                            <Button variant="outline" size="sm">
                              <Eye className="mr-1 h-3.5 w-3.5" />
                              View
                            </Button>
                          </Link>
                          {property.is_published ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => unpublishListing.mutate(property.id)}
                              isLoading={unpublishListing.isPending}
                            >
                              Unpublish
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => publishListing.mutate(property.id)}
                              isLoading={publishListing.isPending}
                            >
                              <Rocket className="mr-1 h-3.5 w-3.5" />
                              Publish
                            </Button>
                          )}
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => {
                              if (confirm(`Archive “${property.name}”?`)) {
                                deleteListing.mutate(property.id);
                              }
                            }}
                            isLoading={deleteListing.isPending}
                          >
                            <Trash2 className="mr-1 h-3.5 w-3.5" />
                            Archive
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-16 text-center">
              <p className="text-lg font-medium text-gray-900">No listings yet</p>
              <p className="mt-2 text-sm text-gray-500">
                Start with a draft, then return here to manage pricing, media, and publish state.
              </p>
              <Link href="/listings/new" className="mt-6 inline-flex">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create first listing
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {data?.total_pages && data.total_pages > 1 ? (
        <div className="flex items-center justify-between rounded-2xl border border-gray-200 bg-white px-4 py-3">
          <Button variant="outline" onClick={() => goToPage(page - 1)} disabled={page <= 1}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>
          <span className="text-sm text-gray-500">
            Page {page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            onClick={() => goToPage(page + 1)}
            disabled={page >= data.total_pages}
          >
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      ) : null}
    </div>
  );
}
