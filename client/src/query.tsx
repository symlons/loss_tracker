import * as React from "react";
import { useCallback } from "react";
import * as echarts from "echarts";
import { default_loading } from "./utils/options";

interface State {
  query_name: string;
  data: Record<string, any>;
  name_s: string[];
}

interface QueryProps {
  state: State;
  setState: React.Dispatch<React.SetStateAction<State>>;
  setQuery: React.Dispatch<
    React.SetStateAction<{ status: boolean; value: string | null }>
  >;
}

export function Query({ state, setState, setQuery }: QueryProps) {
  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const query_name = event.target.value;
      setState((prev: State) => ({ ...prev, query_name }));
      setQuery({ status: true, value: query_name });
    },
    [setState, setQuery],
  );

  const handleSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const chartDom = document.getElementById("main_1")!;
      const myChart = echarts.getInstanceByDom(chartDom)!;
      myChart.showLoading(default_loading);

      try {
        const response = await fetch("/api/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query_name: state.query_name }),
        });

        if (response.ok) {
          const body = await response.json();
          console.log("Query Data received:", body);
        } else {
          console.error("Error fetching query:", response.status);
        }
      } catch (error) {
        console.error("Fetch error:", error);
      } finally {
        myChart.hideLoading();
      }
    },
    [state],
  );

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="query_name"
        onChange={handleChange}
        className="shadow outline-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight"
        id="query_name"
        type="text"
        placeholder="Enter query name"
      />
      <button type="submit" className="btn-submit">
        Submit
      </button>
    </form>
  );
}
