import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../index';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.check(),
    staleTime: 10_000,
    refetchInterval: 30_000,
    retry: true,
    retryDelay: 2000,
  });
}
