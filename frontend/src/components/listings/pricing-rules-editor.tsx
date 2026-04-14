'use client';

import { useMemo, useState } from 'react';
import { CalendarDays, Pencil, Percent, Plus, Trash2 } from 'lucide-react';
import { Button, Input, Skeleton } from '@/components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  formatDateRange,
  formatMoney,
  formatRateType,
} from '@/lib/properties';
import {
  useCreatePricingRule,
  useDeletePricingRule,
  usePropertyPricingRules,
  useUpdatePricingRule,
} from '@/hooks/use-properties';
import type { PricingRule, PricingRuleInput } from '@/types';

const RATE_TYPES = ['daily', 'weekly', 'monthly'];
const DAY_OPTIONS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_TO_INDEX: Record<string, number> = {
  Mon: 0,
  Tue: 1,
  Wed: 2,
  Thu: 3,
  Fri: 4,
  Sat: 5,
  Sun: 6,
};

interface PricingRuleDraft {
  ruleId?: string;
  rate_type: string;
  rate_amount: string;
  currency: string;
  is_peak_rate: boolean;
  peak_start_date: string;
  peak_end_date: string;
  peak_days_of_week: string[];
  discount_percentage: string;
  min_units_for_discount: string;
}

function createEmptyDraft(currency = 'NPR'): PricingRuleDraft {
  return {
    rate_type: 'monthly',
    rate_amount: '',
    currency,
    is_peak_rate: false,
    peak_start_date: '',
    peak_end_date: '',
    peak_days_of_week: [],
    discount_percentage: '',
    min_units_for_discount: '',
  };
}

function draftFromRule(rule: PricingRule): PricingRuleDraft {
  return {
    ruleId: rule.id,
    rate_type: rule.rate_type,
    rate_amount: String(rule.rate_amount),
    currency: rule.currency,
    is_peak_rate: rule.is_peak_rate,
    peak_start_date: rule.peak_start_date ?? '',
    peak_end_date: rule.peak_end_date ?? '',
    peak_days_of_week: rule.peak_days_of_week ?? [],
    discount_percentage:
      rule.discount_percentage === null || rule.discount_percentage === undefined
        ? ''
        : String(rule.discount_percentage),
    min_units_for_discount:
      rule.min_units_for_discount === null || rule.min_units_for_discount === undefined
        ? ''
        : String(rule.min_units_for_discount),
  };
}

function toPayload(draft: PricingRuleDraft): PricingRuleInput {
  return {
    rate_type: draft.rate_type,
    rate_amount: Number(draft.rate_amount),
    currency: draft.currency || 'NPR',
    is_peak_rate: draft.is_peak_rate,
    peak_start_date: draft.is_peak_rate && draft.peak_start_date ? draft.peak_start_date : null,
    peak_end_date: draft.is_peak_rate && draft.peak_end_date ? draft.peak_end_date : null,
    peak_days_of_week_json: draft.is_peak_rate
      ? draft.peak_days_of_week
          .map((day) => DAY_TO_INDEX[day])
          .filter((day): day is number => day !== undefined)
      : [],
    discount_percentage: draft.discount_percentage ? Number(draft.discount_percentage) : null,
    min_units_for_discount: draft.min_units_for_discount ? Number(draft.min_units_for_discount) : null,
  };
}

export function PricingRulesEditor({ propertyId, defaultCurrency = 'NPR' }: { propertyId: string; defaultCurrency?: string }) {
  const { data: rules, isLoading } = usePropertyPricingRules(propertyId);
  const createRule = useCreatePricingRule();
  const updateRule = useUpdatePricingRule();
  const deleteRule = useDeletePricingRule();

  const [draft, setDraft] = useState<PricingRuleDraft>(() => createEmptyDraft(defaultCurrency));
  const [error, setError] = useState<string | null>(null);

  const isSaving = createRule.isPending || updateRule.isPending;
  const currentRules = useMemo(() => rules ?? [], [rules]);

  const resetForm = () => {
    setDraft(createEmptyDraft(defaultCurrency));
    setError(null);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!draft.rate_amount || Number(draft.rate_amount) <= 0) {
      setError('Add a positive rate amount before saving a pricing rule.');
      return;
    }

    if (draft.is_peak_rate && draft.peak_start_date && draft.peak_end_date && draft.peak_end_date < draft.peak_start_date) {
      setError('Peak end date must be on or after the start date.');
      return;
    }

    const payload = toPayload(draft);

    try {
      if (draft.ruleId) {
        await updateRule.mutateAsync({ propertyId, ruleId: draft.ruleId, data: payload });
      } else {
        await createRule.mutateAsync({ propertyId, data: payload });
      }

      resetForm();
    } catch {
      setError('Unable to save this pricing rule right now. Please try again.');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <CalendarDays className="h-5 w-5 text-blue-600" />
          Pricing rules
        </CardTitle>
        <CardDescription>
          Configure monthly, weekly, or daily rates and optional peak-date overrides.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-gray-200 bg-gray-50 p-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Rate type</label>
              <select
                value={draft.rate_type}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, rate_type: event.target.value }))
                }
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {RATE_TYPES.map((option) => (
                  <option key={option} value={option}>
                    {formatRateType(option)}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Rate amount"
              type="number"
              min="0"
              step="0.01"
              value={draft.rate_amount}
              onChange={(event) =>
                setDraft((current) => ({ ...current, rate_amount: event.target.value }))
              }
              placeholder="35000"
            />
            <Input
              label="Currency"
              value={draft.currency}
              onChange={(event) =>
                setDraft((current) => ({ ...current, currency: event.target.value.toUpperCase() }))
              }
              placeholder="NPR"
            />
          </div>

          <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={draft.is_peak_rate}
              onChange={(event) =>
                setDraft((current) => ({ ...current, is_peak_rate: event.target.checked }))
              }
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Treat this as a peak-season rule
          </label>

          {draft.is_peak_rate ? (
            <div className="space-y-4 rounded-xl border border-blue-100 bg-white p-4">
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  label="Peak start date"
                  type="date"
                  value={draft.peak_start_date}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, peak_start_date: event.target.value }))
                  }
                />
                <Input
                  label="Peak end date"
                  type="date"
                  value={draft.peak_end_date}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, peak_end_date: event.target.value }))
                  }
                />
              </div>

              <div>
                <p className="mb-2 text-sm font-medium text-gray-700">Peak weekdays</p>
                <div className="flex flex-wrap gap-2">
                  {DAY_OPTIONS.map((day) => {
                    const selected = draft.peak_days_of_week.includes(day);
                    return (
                      <button
                        key={day}
                        type="button"
                        onClick={() =>
                          setDraft((current) => ({
                            ...current,
                            peak_days_of_week: selected
                              ? current.peak_days_of_week.filter((value) => value !== day)
                              : [...current.peak_days_of_week, day],
                          }))
                        }
                        className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                          selected
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {day}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="Discount percentage"
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={draft.discount_percentage}
              onChange={(event) =>
                setDraft((current) => ({ ...current, discount_percentage: event.target.value }))
              }
              placeholder="5"
            />
            <Input
              label="Minimum units for discount"
              type="number"
              min="1"
              step="1"
              value={draft.min_units_for_discount}
              onChange={(event) =>
                setDraft((current) => ({ ...current, min_units_for_discount: event.target.value }))
              }
              placeholder="3"
            />
          </div>

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Button type="submit" isLoading={isSaving}>
              <Plus className="mr-2 h-4 w-4" />
              {draft.ruleId ? 'Save pricing rule' : 'Add pricing rule'}
            </Button>
            {draft.ruleId ? (
              <Button type="button" variant="outline" onClick={resetForm}>
                Cancel edit
              </Button>
            ) : null}
          </div>
        </form>

        <div className="space-y-3">
          {isLoading ? (
            <>
              <Skeleton className="h-20 w-full rounded-2xl" />
              <Skeleton className="h-20 w-full rounded-2xl" />
            </>
          ) : currentRules.length > 0 ? (
            currentRules.map((rule) => (
              <div
                key={rule.id}
                className="rounded-2xl border border-gray-200 p-4 shadow-sm"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                        {formatRateType(rule.rate_type)}
                      </span>
                      {rule.is_peak_rate ? (
                        <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                          Peak rate
                        </span>
                      ) : null}
                      {rule.discount_percentage ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                          <Percent className="h-3.5 w-3.5" />
                          {rule.discount_percentage}% off
                        </span>
                      ) : null}
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatMoney(rule.rate_amount, rule.currency)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {rule.is_peak_rate
                        ? formatDateRange(rule.peak_start_date, rule.peak_end_date)
                        : 'Applies to standard dates'}
                    </p>
                    {rule.peak_days_of_week?.length ? (
                      <p className="text-sm text-gray-500">
                        Peak weekdays: {rule.peak_days_of_week.join(', ')}
                      </p>
                    ) : null}
                    {rule.min_units_for_discount ? (
                      <p className="text-sm text-gray-500">
                        Discount starts from {rule.min_units_for_discount} units
                      </p>
                    ) : null}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setDraft(draftFromRule(rule))}
                    >
                      <Pencil className="mr-1 h-3.5 w-3.5" />
                      Edit
                    </Button>
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => {
                        if (confirm('Delete this pricing rule?')) {
                          deleteRule.mutate({ propertyId, ruleId: rule.id });
                        }
                      }}
                      isLoading={deleteRule.isPending}
                    >
                      <Trash2 className="mr-1 h-3.5 w-3.5" />
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center">
              <p className="text-sm text-gray-500">
                No pricing rules yet. Add a base monthly, weekly, or daily rate to unlock quotes.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
