import { useQuery } from "@tanstack/react-query";
import { companiesAPI } from "../services/api";

export function useCurrentCompany() {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const cachedName =
    typeof window !== "undefined"
      ? localStorage.getItem("auth_company_name")
      : null;
  const cachedId =
    typeof window !== "undefined"
      ? localStorage.getItem("auth_company_id")
      : null;

  const initialData =
    token && cachedId && cachedName
      ? { name: cachedName, _id: cachedId }
      : undefined;

  const query = useQuery({
    queryKey: ["current-company"],
    queryFn: () => companiesAPI.getCurrent().then((res) => res.data),
    enabled: !!token,
    initialData,
  });

  return {
    company: query.data,
    companyId: query.data?._id ?? null,
    ...query,
  };
}
