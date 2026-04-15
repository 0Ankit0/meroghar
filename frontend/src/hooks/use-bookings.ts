'use client';

import axios from 'axios';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import {
  buildBookingApiParams,
  normalizeBooking,
  normalizeBookingEvents,
  normalizeBookingListResponse,
  normalizeRentalAgreement,
} from '@/lib/bookings';
import type {
  AgreementGeneratePayload,
  BookingCancelPayload,
  BookingEvent,
  BookingListParams,
  BookingListResponse,
  BookingRecord,
  BookingReturnPayload,
  CreateBookingPayload,
  RentalAgreement,
  UpdateBookingPayload,
} from '@/types';

function invalidateBookingQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  bookingId?: string
) {
  queryClient.invalidateQueries({ queryKey: ['bookings'] });

  if (bookingId) {
    queryClient.invalidateQueries({ queryKey: ['bookings', 'detail', bookingId] });
    queryClient.invalidateQueries({ queryKey: ['bookings', 'events', bookingId] });
    queryClient.invalidateQueries({ queryKey: ['bookings', 'agreement', bookingId] });
  }
}

function hasPayload(data: unknown): boolean {
  return data !== null && data !== undefined && data !== '';
}

function toCreateBookingRequest(data: CreateBookingPayload) {
  return {
    property_id: data.property_id,
    rental_start_at: data.rental_start_at,
    rental_end_at: data.rental_end_at,
    special_requests: data.special_requests ?? '',
    payment_method_id: data.payment_method_id,
    quoted_total_fee: data.quoted_total_fee ?? undefined,
    quoted_deposit_amount: data.quoted_deposit_amount ?? undefined,
    quoted_currency: data.quoted_currency ?? undefined,
  };
}

function toUpdateBookingRequest(data: UpdateBookingPayload) {
  return {
    rental_start_at: data.rental_start_at,
    rental_end_at: data.rental_end_at,
    special_requests: data.special_requests,
    quoted_total_fee: data.quoted_total_fee ?? undefined,
    quoted_deposit_amount: data.quoted_deposit_amount ?? undefined,
    quoted_currency: data.quoted_currency ?? undefined,
  };
}

export function useBookings(params?: BookingListParams) {
  return useQuery<BookingListResponse>({
    queryKey: ['bookings', 'list', params],
    queryFn: async () => {
      const response = await apiClient.get<unknown>('/bookings', {
        params: buildBookingApiParams(params),
      });
      return normalizeBookingListResponse(response.data);
    },
  });
}

export function useBooking(bookingId: string) {
  return useQuery<BookingRecord>({
    queryKey: ['bookings', 'detail', bookingId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/bookings/${bookingId}`);
      return normalizeBooking(response.data);
    },
    enabled: Boolean(bookingId),
  });
}

export function useBookingEvents(bookingId: string) {
  return useQuery<BookingEvent[]>({
    queryKey: ['bookings', 'events', bookingId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/bookings/${bookingId}/events`);
      return normalizeBookingEvents(response.data);
    },
    enabled: Boolean(bookingId),
  });
}

export function useBookingAgreement(bookingId: string) {
  return useQuery<RentalAgreement | null>({
    queryKey: ['bookings', 'agreement', bookingId],
    queryFn: async () => {
      try {
        const response = await apiClient.get<unknown>(`/bookings/${bookingId}/agreement`);
        return normalizeRentalAgreement(response.data);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
    enabled: Boolean(bookingId),
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateBookingPayload) => {
      const response = await apiClient.post<unknown>('/bookings', toCreateBookingRequest(data));
      return normalizeBooking(response.data);
    },
    onSuccess: (booking) => {
      invalidateBookingQueries(queryClient, booking.id);
      queryClient.invalidateQueries({ queryKey: ['properties', 'availability', booking.property.id] });
    },
  });
}

export function useUpdateBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      bookingId,
      data,
    }: {
      bookingId: string;
      data: UpdateBookingPayload;
    }) => {
      const response = await apiClient.put<unknown>(
        `/bookings/${bookingId}`,
        toUpdateBookingRequest(data)
      );
      return normalizeBooking(response.data);
    },
    onSuccess: (booking) => {
      invalidateBookingQueries(queryClient, booking.id);
    },
  });
}

export function useConfirmBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ bookingId }: { bookingId: string }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/confirm`);
      return hasPayload(response.data) ? normalizeBooking(response.data) : bookingId;
    },
    onSuccess: (_, variables) => {
      invalidateBookingQueries(queryClient, variables.bookingId);
    },
  });
}

export function useDeclineBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      bookingId,
      data,
    }: {
      bookingId: string;
      data: BookingCancelPayload;
    }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/decline`, data);
      return hasPayload(response.data) ? normalizeBooking(response.data) : bookingId;
    },
    onSuccess: (_, variables) => {
      invalidateBookingQueries(queryClient, variables.bookingId);
    },
  });
}

export function useCancelBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      bookingId,
      data,
    }: {
      bookingId: string;
      data: BookingCancelPayload;
    }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/cancel`, data);
      return hasPayload(response.data) ? normalizeBooking(response.data) : bookingId;
    },
    onSuccess: (_, variables) => {
      invalidateBookingQueries(queryClient, variables.bookingId);
    },
  });
}

export function useReturnBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      bookingId,
      data,
    }: {
      bookingId: string;
      data?: BookingReturnPayload;
    }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/return`, data);
      return hasPayload(response.data) ? normalizeBooking(response.data) : bookingId;
    },
    onSuccess: (_, variables) => {
      invalidateBookingQueries(queryClient, variables.bookingId);
    },
  });
}

export function useGenerateAgreement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      bookingId,
      data,
    }: {
      bookingId: string;
      data?: AgreementGeneratePayload;
    }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/agreement`, {
        template_id: data?.template_id ?? undefined,
        custom_clauses: data?.custom_clauses ?? [],
      });
      return hasPayload(response.data) ? normalizeRentalAgreement(response.data) : null;
    },
    onSuccess: (_, variables) => {
      invalidateBookingQueries(queryClient, variables.bookingId);
    },
  });
}

export function useSendAgreement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ bookingId }: { bookingId: string }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/agreement/send`);
      return hasPayload(response.data) ? normalizeRentalAgreement(response.data) : bookingId;
    },
    onSuccess: (_, variables) => {
      invalidateBookingQueries(queryClient, variables.bookingId);
    },
  });
}

export function useCountersignAgreement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ bookingId }: { bookingId: string }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/agreement/countersign`);
      return hasPayload(response.data) ? normalizeRentalAgreement(response.data) : bookingId;
    },
    onSuccess: (_, variables) => {
      invalidateBookingQueries(queryClient, variables.bookingId);
    },
  });
}
