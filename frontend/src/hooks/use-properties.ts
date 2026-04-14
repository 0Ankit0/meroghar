'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import {
  buildPropertyApiParams,
  normalizeProperty,
  normalizePropertyAvailabilityResponse,
  normalizePropertyCategories,
  normalizePropertyCategoryDetail,
  normalizePropertyListResponse,
  normalizePropertyPhoto,
  normalizePropertyPriceQuote,
  normalizePropertyPricingRules,
} from '@/lib/properties';
import type {
  PricingQuote,
  PricingRule,
  PricingRuleInput,
  PropertyAvailabilityResponse,
  PropertyCategory,
  PropertyCategoryDetail,
  PropertyDetail,
  PropertyListResponse,
  PropertyMutationPayload,
  PropertyPhoto,
  PropertyPhotoUploadPayload,
  PropertyPriceQuoteParams,
  PropertySearchParams,
} from '@/types';

function invalidateListingQueries(queryClient: ReturnType<typeof useQueryClient>, propertyId?: string) {
  queryClient.invalidateQueries({ queryKey: ['properties'] });
  queryClient.invalidateQueries({ queryKey: ['listings'] });

  if (propertyId) {
    queryClient.invalidateQueries({ queryKey: ['properties', 'detail', propertyId] });
    queryClient.invalidateQueries({ queryKey: ['properties', 'pricing-rules', propertyId] });
    queryClient.invalidateQueries({ queryKey: ['properties', 'availability', propertyId] });
  }
}

function toPropertyMutationRequest(data: PropertyMutationPayload) {
  return {
    property_type_id: data.category_id,
    name: data.name,
    description: data.description,
    location_address: data.location_address,
    location_lat: data.location_lat,
    location_lng: data.location_lng,
    deposit_amount: data.deposit_amount,
    min_rental_duration_hours: data.min_rental_duration_hours,
    max_rental_duration_days: data.max_rental_duration_days,
    booking_lead_time_hours: data.booking_lead_time_hours,
    instant_booking_enabled: data.instant_booking_enabled,
    feature_values: data.attribute_values?.map((attribute) => ({
      attribute_id: attribute.attribute_id,
      value: attribute.value,
    })),
    availability_blocks: data.availability_blocks?.map(({ block_type, start_at, end_at, reason }) => ({
      block_type,
      start_at,
      end_at,
      reason: reason ?? '',
    })),
  };
}

export function usePropertyCategories() {
  return useQuery<PropertyCategory[]>({
    queryKey: ['properties', 'categories'],
    queryFn: async () => {
      const response = await apiClient.get<unknown>('/categories');
      return normalizePropertyCategories(response.data);
    },
    staleTime: 60_000,
  });
}

export function usePropertyCategory(categoryId: string) {
  return useQuery<PropertyCategoryDetail>({
    queryKey: ['properties', 'categories', categoryId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/categories/${categoryId}`);
      return normalizePropertyCategoryDetail(response.data);
    },
    enabled: Boolean(categoryId),
    staleTime: 60_000,
  });
}

export function usePropertySearch(params?: PropertySearchParams) {
  return useQuery<PropertyListResponse>({
    queryKey: ['properties', 'search', params],
    queryFn: async () => {
      const response = await apiClient.get<unknown>('/assets', {
        params: buildPropertyApiParams(params),
      });
      return normalizePropertyListResponse(response.data);
    },
  });
}

export function useLandlordListings(params?: PropertySearchParams) {
  return useQuery<PropertyListResponse>({
    queryKey: ['listings', 'mine', params],
    queryFn: async () => {
      const response = await apiClient.get<unknown>('/properties/mine', {
        params: buildPropertyApiParams(params),
      });
      return normalizePropertyListResponse(response.data);
    },
  });
}

export function useProperty(propertyId: string) {
  return useQuery<PropertyDetail>({
    queryKey: ['properties', 'detail', propertyId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/properties/${propertyId}`);
      return normalizeProperty(response.data);
    },
    enabled: Boolean(propertyId),
  });
}

export function usePropertyAvailability(propertyId: string, params?: PropertySearchParams) {
  return useQuery<PropertyAvailabilityResponse>({
    queryKey: ['properties', 'availability', propertyId, params],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/properties/${propertyId}/availability`, {
        params: buildPropertyApiParams(params),
      });
      return normalizePropertyAvailabilityResponse(response.data, propertyId);
    },
    enabled: Boolean(propertyId),
  });
}

export function usePropertyPriceQuote(propertyId: string, params?: PropertyPriceQuoteParams) {
  return useQuery<PricingQuote>({
    queryKey: ['properties', 'price', propertyId, params],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/properties/${propertyId}/price`, {
        params: buildPropertyApiParams(params),
      });
      return normalizePropertyPriceQuote(response.data, { preferDueNow: true });
    },
    enabled: Boolean(propertyId && params?.start && params?.end),
  });
}

export function usePropertyPricingRules(propertyId: string) {
  return useQuery<PricingRule[]>({
    queryKey: ['properties', 'pricing-rules', propertyId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/properties/${propertyId}/pricing-rules`);
      return normalizePropertyPricingRules(response.data);
    },
    enabled: Boolean(propertyId),
  });
}

export function useCreateListing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: PropertyMutationPayload) => {
      const response = await apiClient.post<unknown>('/assets', toPropertyMutationRequest(data));
      return normalizeProperty(response.data);
    },
    onSuccess: (property) => {
      invalidateListingQueries(queryClient, property.id);
    },
  });
}

export function useUpdateListing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ propertyId, data }: { propertyId: string; data: PropertyMutationPayload }) => {
      const response = await apiClient.put<unknown>(
        `/properties/${propertyId}`,
        toPropertyMutationRequest(data)
      );
      return normalizeProperty(response.data);
    },
    onSuccess: (property) => {
      invalidateListingQueries(queryClient, property.id);
    },
  });
}

export function useDeleteListing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (propertyId: string) => {
      await apiClient.delete(`/properties/${propertyId}`);
      return propertyId;
    },
    onSuccess: (propertyId) => {
      invalidateListingQueries(queryClient, propertyId);
    },
  });
}

export function usePublishListing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (propertyId: string) => {
      const response = await apiClient.post<unknown>(`/properties/${propertyId}/publish`);
      return normalizeProperty(response.data);
    },
    onSuccess: (property) => {
      invalidateListingQueries(queryClient, property.id);
    },
  });
}

export function useUnpublishListing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (propertyId: string) => {
      const response = await apiClient.post<unknown>(`/properties/${propertyId}/unpublish`);
      return normalizeProperty(response.data);
    },
    onSuccess: (property) => {
      invalidateListingQueries(queryClient, property.id);
    },
  });
}

export function useCreatePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ propertyId, data }: { propertyId: string; data: PricingRuleInput }) => {
      const response = await apiClient.post<unknown>(`/properties/${propertyId}/pricing-rules`, data);
      return normalizePropertyPricingRules([response.data])[0] as PricingRule;
    },
    onSuccess: (_, variables) => {
      invalidateListingQueries(queryClient, variables.propertyId);
    },
  });
}

export function useUpdatePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      propertyId,
      ruleId,
      data,
    }: {
      propertyId: string;
      ruleId: string;
      data: PricingRuleInput;
    }) => {
      const response = await apiClient.put<unknown>(
        `/properties/${propertyId}/pricing-rules/${ruleId}`,
        data
      );
      return normalizePropertyPricingRules([response.data])[0] as PricingRule;
    },
    onSuccess: (_, variables) => {
      invalidateListingQueries(queryClient, variables.propertyId);
    },
  });
}

export function useDeletePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ propertyId, ruleId }: { propertyId: string; ruleId: string }) => {
      await apiClient.delete(`/properties/${propertyId}/pricing-rules/${ruleId}`);
      return { propertyId, ruleId };
    },
    onSuccess: ({ propertyId }) => {
      invalidateListingQueries(queryClient, propertyId);
    },
  });
}

export function useUploadPropertyPhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      propertyId,
      data,
    }: {
      propertyId: string;
      data: PropertyPhotoUploadPayload;
    }) => {
      const formData = new FormData();
      formData.append('file', data.file);
      if (data.caption) {
        formData.append('caption', data.caption);
      }
      if (typeof data.is_cover === 'boolean') {
        formData.append('is_cover', String(data.is_cover));
      }
      if (typeof data.position === 'number') {
        formData.append('position', String(data.position));
      }

      const response = await apiClient.post<unknown>(`/properties/${propertyId}/photos`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return normalizePropertyPhoto(response.data) as PropertyPhoto;
    },
    onSuccess: (_, variables) => {
      invalidateListingQueries(queryClient, variables.propertyId);
    },
  });
}

export function useDeletePropertyPhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ propertyId, photoId }: { propertyId: string; photoId: string }) => {
      await apiClient.delete(`/properties/${propertyId}/photos/${photoId}`);
      return { propertyId, photoId };
    },
    onSuccess: ({ propertyId }) => {
      invalidateListingQueries(queryClient, propertyId);
    },
  });
}
