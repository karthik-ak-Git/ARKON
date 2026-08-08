import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiApi } from '../index';
import type { AIProviderCreate, AIProviderUpdate } from '../index';

export function useAIProviders() {
  return useQuery({
    queryKey: ['ai', 'providers'],
    queryFn: () => aiApi.listProviders(),
    staleTime: 30_000,
  });
}

export function useAIProviderHealth() {
  return useQuery({
    queryKey: ['ai', 'providers', 'health'],
    queryFn: () => aiApi.getAllProvidersHealth(),
    staleTime: 60_000,
    refetchInterval: 120_000, // 2 minutes instead of 30 seconds
    refetchIntervalInBackground: false,
  });
}

export function useAIRouting() {
  return useQuery({
    queryKey: ['ai', 'routing'],
    queryFn: () => aiApi.getRoutingPolicy(),
    staleTime: 30_000,
  });
}

export function useAIModels(providerId?: string) {
  return useQuery({
    queryKey: ['ai', 'models', providerId],
    queryFn: () => aiApi.listModels(providerId),
    staleTime: 60_000,
  });
}

export function useRegisterAIProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AIProviderCreate) => aiApi.registerProvider(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai', 'providers'] }),
  });
}

export function useUpdateAIProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ providerId, data }: { providerId: string; data: AIProviderUpdate }) =>
      aiApi.updateProvider(providerId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai', 'providers'] }),
  });
}

export function useEnableAIProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (providerId: string) => aiApi.enableProvider(providerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai', 'providers'] }),
  });
}

export function useDisableAIProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (providerId: string) => aiApi.disableProvider(providerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai', 'providers'] }),
  });
}

export function useDeleteAIProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (providerId: string) => aiApi.deleteProvider(providerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai', 'providers'] }),
  });
}

export function useDetectLocalProviders() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => aiApi.detectLocalProviders(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai', 'providers'] }),
  });
}

export function useSetAIRoutingPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { policy: string; manual_provider_id?: string }) =>
      aiApi.setRoutingPolicy(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai', 'routing'] }),
  });
}

export function useAIChat() {
  return useMutation({
    mutationFn: (data: Parameters<typeof aiApi.chat>[0]) => aiApi.chat(data),
  });
}
