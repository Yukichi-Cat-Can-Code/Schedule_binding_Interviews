import { useQuery } from "@tanstack/react-query";
import { companiesAPI } from "../services/api";

/**
 * Central hook to resolve the current company from backend.
 * - Uses /companies/current/ so it is always consistent with the auth token.
 * - Keeps localStorage.auth_company_id in sync for legacy callers.
 */
export const useCurrentCompany = () => {
  const {
    data: company,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["company", "current"],
    queryFn: async () => {
      const res = await companiesAPI.getCurrent();
      const doc = res.data;
      if (doc && doc._id) {
        localStorage.setItem("auth_company_id", doc._id);
      }
      return doc;
    },
  });

  return {
    company,
    companyId: company?._id || null,
    isLoading,
    isError,
    error,
  };
};
