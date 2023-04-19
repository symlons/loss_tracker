import * as React from "react";

function Store(state) {
  async function save_data() {
    let data = state.data;
    let name = state.name;
    let name_s = state.name_s;
    let response = await fetch("/api/store", {
      method: "POST", // or 'PUT',
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ data, name, name_s }),
    });
    let body = await response.text();
    console.log(body)
  }

  return (
    <>
      <button
        className="bg-white hover:bg-black hover:text-white font-bold py-2 px-2 rounded border-2 border-black mb-4"
        onClick={save_data}
      >
        Store results
      </button>
    </>
  );
}

export { Store };
