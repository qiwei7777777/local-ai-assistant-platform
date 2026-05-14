"use client";

import { useCallback, useEffect, useState } from "react";

type AsyncState<T> = {
  data: T | null;
  error: string | null;
  isLoading: boolean;
};

export function useAsyncResource<T>(
  loader: () => Promise<T>,
  deps: ReadonlyArray<unknown> = [],
) {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    isLoading: true,
  });

  const reload = useCallback(async () => {
    setState({ data: null, error: null, isLoading: true });
    try {
      const data = await loader();
      setState({ data, error: null, isLoading: false });
    } catch (error) {
      setState({
        data: null,
        error: error instanceof Error ? error.message : "Request failed.",
        isLoading: false,
      });
    }
  }, deps);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    ...state,
    reload,
  };
}
