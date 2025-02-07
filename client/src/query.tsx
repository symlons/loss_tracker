import * as React from "react"; // Correctly import React
import { useCallback } from "react"; // Import useCallback separately
import * as echarts from "echarts";
import { default_loading } from "./utils/options";

interface QueryProps {
  state: {
    query_name: string;
    data: Record<string, any>;
    name_s: string[];
  };
  setState: React.Dispatch<React.SetStateAction<any>>;
  setQuery: React.Dispatch<React.SetStateAction<{ status: boolean; value: string | null }>>;
}

export function Query({ state, setState, setQuery }: QueryProps) {
  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const query_name = event.target.value.toString();
    setState((prevState) => ({
      ...prevState,
      query_name,
      query: true,
    }));
    setQuery({ status: false, value: query_name });
  }, [setState, setQuery]);

  const handleSubmit = useCallback(async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const { query_name } = state;

    const chartDom = document.getElementById("main_1")!;
    const myChart = echarts.getInstanceByDom(chartDom)!;
    myChart.showLoading(default_loading);

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        credentials: "omit",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query_name }),
      });

      if (response.ok) {
        const body = await response.json();
        // Handle the response...
      } else {
        console.error("Error fetching data:", response.status);
      }
    } catch (error) {
      console.error("Fetch error:", error);
    } finally {
      myChart.hideLoading();
    }
  }, [state, setState, setQuery]);

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="query_name"
        onChange={handleChange}
        className="shadow outline-none appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight"
        id="query_name"
        type="text"
        placeholder="query_name"
      />
    </form>
  );
}
