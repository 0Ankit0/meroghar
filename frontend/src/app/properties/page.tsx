'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, Building2, Search } from 'lucide-react';
import { Button, Input, Skeleton } from '@/components/ui';
import { Card, CardContent } from '@/components/ui/card';
import { PropertyCard } from '@/components/listings/property-card';
import { usePropertyCategories, usePropertySearch } from '@/hooks/use-properties';
import { toDateTimeLocalValue } from '@/lib/properties';
import { useAuthStore } from '@/store/auth-store';

interface SearchFormState {
  category: string;
  start: string;
  end: string;
  location: string;
  radius_km: string;
  min_price: string;
  max_price: string;
}

function parseNumber(value: string | null) {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function buildFormState(params: Pick<URLSearchParams, 'get'>): SearchFormState {
  return {
    category: params.get('category') ?? '',
    start: toDateTimeLocalValue(params.get('start')) || params.get('start') || '',
    end: toDateTimeLocalValue(params.get('end')) || params.get('end') || '',
    location: params.get('location') ?? '',
    radius_km: params.get('radius_km') ?? '',
    min_price: params.get('min_price') ?? '',
    max_price: params.get('max_price') ?? '',
  };
}

function buildQueryString(filters: SearchFormState, page = 1) {
  const params = new URLSearchParams();

  if (filters.category) params.set('category', filters.category);
  if (filters.start) params.set('start', filters.start);
  if (filters.end) params.set('end', filters.end);
  if (filters.location) params.set('location', filters.location);
  if (filters.radius_km) params.set('radius_km', filters.radius_km);
  if (filters.min_price) params.set('min_price', filters.min_price);
  if (filters.max_price) params.set('max_price', filters.max_price);
  if (page > 1) params.set('page', String(page));

  return params.toString();
}

export default function PropertiesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchKey = searchParams.toString();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const [filters, setFilters] = useState<SearchFormState>(() => buildFormState(searchParams));

  useEffect(() => {
    setFilters(buildFormState(searchParams));
  }, [searchKey, searchParams]);

  const queryParams = useMemo(
    () => ({
      category: searchParams.get('category') || undefined,
      start: searchParams.get('start') || undefined,
      end: searchParams.get('end') || undefined,
      location: searchParams.get('location') || undefined,
      radius_km: parseNumber(searchParams.get('radius_km')),
      min_price: parseNumber(searchParams.get('min_price')),
      max_price: parseNumber(searchParams.get('max_price')),
      page: parseNumber(searchParams.get('page')) ?? 1,
      per_page: 12,
    }),
    [searchParams]
  );

  const { data: categories } = usePropertyCategories();
  const { data, isLoading, error } = usePropertySearch(queryParams);

  const currentPage = queryParams.page ?? 1;

  const applyFilters = (page = 1) => {
    const query = buildQueryString(filters, page);
    router.push(query ? `/properties?${query}` : '/properties');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-blue-600">
            <Building2 className="h-5 w-5" />
            MeroGhar
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost">Home</Button>
            </Link>
            <Link href={isAuthenticated ? '/dashboard' : '/login'}>
              <Button>{isAuthenticated ? 'Open dashboard' : 'Sign in'}</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <section className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700">
            <Search className="h-4 w-4" />
            Public property search
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-gray-900">Find available homes</h1>
          <p className="max-w-3xl text-lg text-gray-600">
            Search published listings by property type, price, location, and move-in window. Pricing
            quotes stay consistent with the same dates you use on detail pages.
          </p>
        </section>

        <Card className="shadow-sm">
          <CardContent className="space-y-4 pt-6">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Property type</label>
                <select
                  value={filters.category}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, category: event.target.value }))
                  }
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All property types</option>
                  {(categories ?? []).map((category) => (
                    <option key={category.id} value={category.slug}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <Input
                label="Location"
                value={filters.location}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, location: event.target.value }))
                }
                placeholder="Kathmandu, Pokhara, Lalitpur…"
              />
              <Input
                label="Move-in"
                type="datetime-local"
                value={filters.start}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, start: event.target.value }))
                }
              />
              <Input
                label="Move-out"
                type="datetime-local"
                value={filters.end}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, end: event.target.value }))
                }
              />
              <Input
                label="Radius (km)"
                type="number"
                min="1"
                step="1"
                value={filters.radius_km}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, radius_km: event.target.value }))
                }
                placeholder="5"
              />
              <Input
                label="Minimum price"
                type="number"
                min="0"
                step="0.01"
                value={filters.min_price}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, min_price: event.target.value }))
                }
                placeholder="25000"
              />
              <Input
                label="Maximum price"
                type="number"
                min="0"
                step="0.01"
                value={filters.max_price}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, max_price: event.target.value }))
                }
                placeholder="80000"
              />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={() => applyFilters()}>
                <Search className="mr-2 h-4 w-4" />
                Search listings
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setFilters({
                    category: '',
                    start: '',
                    end: '',
                    location: '',
                    radius_km: '',
                    min_price: '',
                    max_price: '',
                  });
                  router.push('/properties');
                }}
              >
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        <section className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">Search results</h2>
              <p className="text-sm text-gray-500">
                {data ? `${data.total} published listings found` : 'Browse available properties'}
              </p>
            </div>
            {data?.total_pages && data.total_pages > 1 ? (
              <div className="text-sm text-gray-500">
                Page {currentPage} of {data.total_pages}
              </div>
            ) : null}
          </div>

          {isLoading ? (
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((key) => (
                <Skeleton key={key} className="h-[420px] w-full rounded-2xl" />
              ))}
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-6 py-8 text-sm text-red-700">
              Unable to load listings right now. Please retry in a moment.
            </div>
          ) : data?.items.length ? (
            <>
              <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
                {data.items.map((property) => {
                  const detailQuery = new URLSearchParams();
                  if (filters.start) detailQuery.set('start', filters.start);
                  if (filters.end) detailQuery.set('end', filters.end);

                  const href = detailQuery.toString()
                    ? `/properties/${property.id}?${detailQuery.toString()}`
                    : `/properties/${property.id}`;

                  return <PropertyCard key={property.id} property={property} href={href} />;
                })}
              </div>

              {data.total_pages > 1 ? (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3">
                  <Button
                    variant="outline"
                    onClick={() => applyFilters(Math.max(1, currentPage - 1))}
                    disabled={currentPage <= 1}
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Previous
                  </Button>
                  <span className="text-sm text-gray-500">
                    Showing page {currentPage} of {data.total_pages}
                  </span>
                  <Button
                    variant="outline"
                    onClick={() => applyFilters(currentPage + 1)}
                    disabled={currentPage >= data.total_pages}
                  >
                    Next
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              ) : null}
            </>
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-16 text-center">
              <p className="text-lg font-medium text-gray-900">No listings matched that search.</p>
              <p className="mt-2 text-sm text-gray-500">
                Try a broader location, remove the price filter, or adjust your dates.
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
