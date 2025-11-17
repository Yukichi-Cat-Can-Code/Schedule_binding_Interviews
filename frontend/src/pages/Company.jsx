import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { companiesAPI } from "../services/api";
import toast from "react-hot-toast";

const Company = () => {
  const [company, setCompany] = useState(null);
  const [form, setForm] = useState({ name: "", code: "" });
  const [companyId, setCompanyId] = useState(() =>
    localStorage.getItem("auth_company_id")
  );

  const queryClient = useQueryClient();

  const { data: fetchedCompany, isLoading } = useQuery({
    queryKey: ["company", "current"],
    enabled: true,
    queryFn: async () => {
      const res = await companiesAPI.getCurrent();
      const doc = res.data;
      if (doc && doc._id) {
        localStorage.setItem("auth_company_id", doc._id);
        setCompanyId(doc._id);
      }
      return doc;
    },
  });

  useEffect(() => {
    if (fetchedCompany) {
      setCompany(fetchedCompany);
      setForm({
        name: fetchedCompany.name || "",
        code: fetchedCompany.code || "",
      });
    }
  }, [fetchedCompany]);

  const save = async (e) => {
    e.preventDefault();
    try {
      await companiesAPI.update(companyId, form);
      toast.success("Company updated");
      // invalidate cached company & companies list
      queryClient.invalidateQueries({ queryKey: ["company", companyId] });
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      // dispatch custom event so header badge can refresh if needed
      window.dispatchEvent(new Event("company-updated"));
    } catch (e) {
      toast.error(e.message || "Failed to update");
    }
  };

  if (!companyId) {
    return <div>Please login to manage company.</div>;
  }
  if (isLoading) {
    return <div>Loading company...</div>;
  }

  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-semibold mb-4">Company</h2>
      <form onSubmit={save} className="space-y-4 bg-white p-6 rounded shadow">
        <div>
          <label className="block text-sm mb-1">Name</label>
          <input
            className="w-full border px-3 py-2 rounded"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Code</label>
          <input
            className="w-full border px-3 py-2 rounded"
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value })}
            required
          />
        </div>
        <div className="flex justify-end">
          <button type="submit" className="btn btn-primary">
            Save
          </button>
        </div>
      </form>
    </div>
  );
};

export default Company;
