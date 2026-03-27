'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth-store';
import { useNotificationDevices, useNotificationPreferences, usePushConfig, useRegisterNotificationDevice, useSystemCapabilities } from '@/hooks';
import { registerCurrentPushDevice } from '@/lib/push-registration';

export function TemplateRuntimeProvider({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { data: capabilities } = useSystemCapabilities();
  const { data: pushConfig } = usePushConfig();
  const { data: preferences } = useNotificationPreferences({ enabled: isAuthenticated });
  const { data: devices } = useNotificationDevices({ enabled: isAuthenticated });
  const registerDevice = useRegisterNotificationDevice();

  const notificationsEnabled = capabilities?.modules.notifications ?? true;
  const activePushProvider = pushConfig?.provider;
  const fallbackPushProviders = capabilities?.fallback_providers?.push ?? [];
  const providerPriority = [activePushProvider, ...fallbackPushProviders].filter(
    (provider, index, list): provider is string =>
      Boolean(provider) && list.indexOf(provider) === index
  );
  const shouldRegisterPush = Boolean(
    isAuthenticated &&
      notificationsEnabled &&
      preferences?.push_enabled &&
      providerPriority.length > 0
  );
  const hasMatchingDevice = providerPriority.some((provider) =>
    Boolean(devices?.some((device) => device.provider === provider && device.is_active))
  );

  useEffect(() => {
    if (!shouldRegisterPush || !pushConfig || hasMatchingDevice || registerDevice.isPending) {
      return;
    }

    let cancelled = false;

    const syncDevice = async () => {
      for (const provider of providerPriority) {
        if (!pushConfig.providers[provider as keyof typeof pushConfig.providers]?.enabled) {
          continue;
        }
        const payload = await registerCurrentPushDevice(provider, pushConfig);
        if (!cancelled && payload) {
          await registerDevice.mutateAsync(payload);
          break;
        }
      }
    };

    void syncDevice();

    return () => {
      cancelled = true;
    };
  }, [hasMatchingDevice, providerPriority, pushConfig, registerDevice, shouldRegisterPush]);

  return <>{children}</>;
}
