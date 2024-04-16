import { set_option } from "./options";

function calc_max(state: { name; data }, query: { status; value }) {
  let value;
  if (state.name === undefined || query.value !== "") {
    if (state.data[query.value] !== undefined) {
      value =
        state.data[query.value][state.data[query.value].length - 1].value[0];
    }
  }
  return value;
}

export function update_data(state, query) {
  let option, new_name, new_data;
  let max = calc_max(state, query);

  if (query.status === false) {
	  console.log('firstasdfjksj')
    new_name = state.name;
    new_data = state.data[new_name];
    option = set_option(max, new_name, new_data);
  } else if (query.status === true && query.value !== undefined) {
    new_name = query.value;
    new_data = state.data[query.value];
    option = set_option(max, new_name, new_data);
  } else {
    console.log("query status set to true, but no data was provided");
    return null;
  }
  return option;
}
